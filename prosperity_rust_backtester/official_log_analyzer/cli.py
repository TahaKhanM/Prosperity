#!/usr/bin/env python3
"""Analyze official IMC Prosperity log bundles.

This script is designed for hosted backtester zip bundles that contain:
- a `.log` JSON blob with `activitiesLog`, `tradeHistory`, and per-tick logs
- a `.json` summary with `profit`, `graphLog`, and final positions

It can also replay a local trader file against the official activity snapshots
using a lightweight in-script datamodel shim. That lets us compare intended
orders to actual official fills, which is especially useful for deterministic
probe traders.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import sys
import types
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


PRODUCTS = ["ASH_COATED_OSMIUM", "INTARIAN_PEPPER_ROOT"]
HORIZONS = [1, 5, 10, 20]
XIRECS = "XIRECS"


@dataclass
class BookSnapshot:
    day: int
    timestamp: int
    product: str
    bid_prices: List[int]
    bid_volumes: List[int]
    ask_prices: List[int]
    ask_volumes: List[int]
    mid_price: float
    profit_and_loss: float

    @property
    def bid1(self) -> Optional[int]:
        return self.bid_prices[0] if self.bid_prices else None

    @property
    def ask1(self) -> Optional[int]:
        return self.ask_prices[0] if self.ask_prices else None

    @property
    def spread(self) -> Optional[int]:
        if self.bid1 is None or self.ask1 is None:
            return None
        return self.ask1 - self.bid1

    def level(self, side: str, level: int) -> Optional[int]:
        prices = self.bid_prices if side == "bid" else self.ask_prices
        if level < len(prices):
            return prices[level]
        return None


def parse_number(value: object, *, as_int: bool = False) -> Optional[float]:
    if value in ("", None):
        return None
    number = float(value)
    if as_int:
        return int(round(number))
    return number


def infer_run_label(path: Path) -> str:
    return path.stem


def discover_input_paths(paths: Iterable[Path]) -> List[Path]:
    discovered: List[Path] = []
    for path in paths:
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix in {".zip", ".json", ".log"}:
                    discovered.append(child)
        elif path.is_file():
            discovered.append(path)
    # Keep first occurrence if duplicate paths are provided.
    unique: Dict[str, Path] = {}
    for path in discovered:
        unique[str(path.resolve())] = path
    return list(unique.values())


def merge_payloads(*payloads: Dict[str, object]) -> Dict[str, object]:
    merged: Dict[str, object] = {}
    for payload in payloads:
        merged.update(payload)
    return merged


def load_payload(path: Path) -> Dict[str, object]:
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            log_payload = {}
            json_payload = {}
            for name in archive.namelist():
                if name.endswith(".log"):
                    log_payload = json.loads(archive.read(name))
                elif name.endswith(".json"):
                    json_payload = json.loads(archive.read(name))
            return merge_payloads(json_payload, log_payload)
    return json.loads(path.read_text())


def parse_activities_log(activities_log: str) -> Dict[str, Dict[int, BookSnapshot]]:
    books: Dict[str, Dict[int, BookSnapshot]] = defaultdict(dict)
    reader = csv.DictReader(io.StringIO(activities_log), delimiter=";")
    for row in reader:
        product = str(row["product"])
        bid_prices: List[int] = []
        bid_volumes: List[int] = []
        ask_prices: List[int] = []
        ask_volumes: List[int] = []
        for level in range(1, 4):
            bid_price = parse_number(row.get(f"bid_price_{level}"), as_int=True)
            bid_volume = parse_number(row.get(f"bid_volume_{level}"), as_int=True)
            ask_price = parse_number(row.get(f"ask_price_{level}"), as_int=True)
            ask_volume = parse_number(row.get(f"ask_volume_{level}"), as_int=True)
            if bid_price is not None and bid_volume is not None:
                bid_prices.append(int(bid_price))
                bid_volumes.append(int(bid_volume))
            if ask_price is not None and ask_volume is not None:
                ask_prices.append(int(ask_price))
                ask_volumes.append(int(abs(ask_volume)))

        snapshot = BookSnapshot(
            day=int(parse_number(row.get("day"), as_int=True) or 0),
            timestamp=int(parse_number(row.get("timestamp"), as_int=True) or 0),
            product=product,
            bid_prices=bid_prices,
            bid_volumes=bid_volumes,
            ask_prices=ask_prices,
            ask_volumes=ask_volumes,
            mid_price=float(parse_number(row.get("mid_price")) or 0.0),
            profit_and_loss=float(parse_number(row.get("profit_and_loss")) or 0.0),
        )
        books[product][snapshot.timestamp] = snapshot
    return books


def parse_graph_log(graph_log: str) -> List[Tuple[int, float]]:
    if not graph_log:
        return []
    rows: List[Tuple[int, float]] = []
    reader = csv.DictReader(io.StringIO(graph_log), delimiter=";")
    for row in reader:
        rows.append(
            (
                int(parse_number(row.get("timestamp"), as_int=True) or 0),
                float(parse_number(row.get("value")) or 0.0),
            )
        )
    return rows


def product_final_pnl(books: Dict[str, Dict[int, BookSnapshot]]) -> Dict[str, float]:
    final: Dict[str, float] = {}
    for product, by_ts in books.items():
        if not by_ts:
            continue
        last_ts = max(by_ts)
        final[product] = by_ts[last_ts].profit_and_loss
    return final


def submission_side(trade: Dict[str, object]) -> Optional[str]:
    if trade.get("buyer") == "SUBMISSION":
        return "buy"
    if trade.get("seller") == "SUBMISSION":
        return "sell"
    return None


def infer_external_side(trade: Dict[str, object], snapshot: BookSnapshot) -> str:
    price = int(round(float(trade["price"])))
    if snapshot.ask1 is not None and price >= snapshot.ask1:
        return "buy"
    if snapshot.bid1 is not None and price <= snapshot.bid1:
        return "sell"
    if snapshot.ask1 is None:
        return "sell"
    if snapshot.bid1 is None:
        return "buy"
    ask_gap = abs(snapshot.ask1 - price)
    bid_gap = abs(price - snapshot.bid1)
    return "buy" if ask_gap < bid_gap else "sell"


def classify_submission_trade(trade: Dict[str, object], snapshot: BookSnapshot) -> str:
    price = int(round(float(trade["price"])))
    side = submission_side(trade)
    if side is None:
        return "non_submission"
    if side == "buy":
        for level, ask in enumerate(snapshot.ask_prices, start=1):
            if price == ask:
                return f"take_a{level}"
        if snapshot.bid1 is not None and snapshot.ask1 is not None and snapshot.bid1 < price < snapshot.ask1:
            return "passive_inside_buy"
        if snapshot.bid1 is not None and price <= snapshot.bid1:
            return "passive_join_buy"
        return "other_buy"
    for level, bid in enumerate(snapshot.bid_prices, start=1):
        if price == bid:
            return f"take_b{level}"
    if snapshot.bid1 is not None and snapshot.ask1 is not None and snapshot.bid1 < price < snapshot.ask1:
        return "passive_inside_sell"
    if snapshot.ask1 is not None and price >= snapshot.ask1:
        return "passive_join_sell"
    return "other_sell"


def favorable_markout(side: str, trade_price: float, future_mid: Optional[float]) -> Optional[float]:
    if future_mid is None:
        return None
    if side == "buy":
        return future_mid - trade_price
    return trade_price - future_mid


def favorable_next_mid_move(side: str, current_mid: float, future_mid: Optional[float]) -> Optional[float]:
    if future_mid is None:
        return None
    if side == "buy":
        return future_mid - current_mid
    return current_mid - future_mid


def favorable_same_side_level_move(side: str, before: BookSnapshot, after: Optional[BookSnapshot]) -> Optional[float]:
    if after is None:
        return None
    if side == "buy":
        if before.ask1 is None or after.ask1 is None:
            return None
        return after.ask1 - before.ask1
    if before.bid1 is None or after.bid1 is None:
        return None
    return before.bid1 - after.bid1


def favorable_opp_side_level_move(side: str, before: BookSnapshot, after: Optional[BookSnapshot]) -> Optional[float]:
    if after is None:
        return None
    if side == "buy":
        if before.bid1 is None or after.bid1 is None:
            return None
        return after.bid1 - before.bid1
    if before.ask1 is None or after.ask1 is None:
        return None
    return before.ask1 - after.ask1


def mean(values: Iterable[float]) -> Optional[float]:
    values = list(values)
    if not values:
        return None
    return sum(values) / len(values)


def round_or_none(value: Optional[float], digits: int = 3) -> Optional[float]:
    if value is None:
        return None
    return round(value, digits)


def positions_before_timestamp(trades: List[Dict[str, object]]) -> Dict[int, Dict[str, int]]:
    by_ts: Dict[int, Dict[str, int]] = {}
    position = defaultdict(int)
    timestamps = sorted({int(trade["timestamp"]) for trade in trades})
    grouped: Dict[int, List[Dict[str, object]]] = defaultdict(list)
    for trade in trades:
        grouped[int(trade["timestamp"])].append(trade)
    for timestamp in timestamps:
        by_ts[timestamp] = dict(position)
        for trade in grouped[timestamp]:
            side = submission_side(trade)
            if side == "buy":
                position[str(trade["symbol"])] += int(trade["quantity"])
            elif side == "sell":
                position[str(trade["symbol"])] -= int(trade["quantity"])
    return by_ts


def build_trade_lookup(
    trades: List[Dict[str, object]]
) -> Tuple[Dict[Tuple[int, str, str, int], int], Dict[int, Dict[str, List[Dict[str, object]]]], Dict[int, Dict[str, List[Dict[str, object]]]]]:
    submission_qty: Dict[Tuple[int, str, str, int], int] = defaultdict(int)
    own_by_ts: Dict[int, Dict[str, List[Dict[str, object]]]] = defaultdict(lambda: defaultdict(list))
    market_by_ts: Dict[int, Dict[str, List[Dict[str, object]]]] = defaultdict(lambda: defaultdict(list))
    for trade in trades:
        timestamp = int(trade["timestamp"])
        product = str(trade["symbol"])
        price = int(round(float(trade["price"])))
        side = submission_side(trade)
        if side is not None:
            submission_qty[(timestamp, product, side, price)] += int(trade["quantity"])
            own_by_ts[timestamp][product].append(trade)
        else:
            market_by_ts[timestamp][product].append(trade)
    return submission_qty, own_by_ts, market_by_ts


def make_lightweight_datamodel() -> types.ModuleType:
    module = types.ModuleType("datamodel")

    class Listing:
        def __init__(self, symbol: str, product: str, denomination: str):
            self.symbol = symbol
            self.product = product
            self.denomination = denomination

    class Observation:
        def __init__(self, plainValueObservations: Dict[str, int], conversionObservations: Dict[str, object]):
            self.plainValueObservations = plainValueObservations
            self.conversionObservations = conversionObservations

    class Order:
        def __init__(self, symbol: str, price: int, quantity: int):
            self.symbol = symbol
            self.price = price
            self.quantity = quantity

        def __repr__(self) -> str:
            return f"({self.symbol}, {self.price}, {self.quantity})"

    class OrderDepth:
        def __init__(self):
            self.buy_orders: Dict[int, int] = {}
            self.sell_orders: Dict[int, int] = {}

    class Trade:
        def __init__(
            self,
            symbol: str,
            price: int,
            quantity: int,
            buyer: str = "",
            seller: str = "",
            timestamp: int = 0,
        ):
            self.symbol = symbol
            self.price = price
            self.quantity = quantity
            self.buyer = buyer
            self.seller = seller
            self.timestamp = timestamp

    class TradingState:
        def __init__(
            self,
            traderData: str,
            timestamp: int,
            listings: Dict[str, Listing],
            order_depths: Dict[str, OrderDepth],
            own_trades: Dict[str, List[Trade]],
            market_trades: Dict[str, List[Trade]],
            position: Dict[str, int],
            observations: Observation,
        ):
            self.traderData = traderData
            self.timestamp = timestamp
            self.listings = listings
            self.order_depths = order_depths
            self.own_trades = own_trades
            self.market_trades = market_trades
            self.position = position
            self.observations = observations

    module.Listing = Listing
    module.Observation = Observation
    module.Order = Order
    module.OrderDepth = OrderDepth
    module.Trade = Trade
    module.TradingState = TradingState
    return module


def load_trader_module(trader_path: Path):
    shim = make_lightweight_datamodel()
    previous = sys.modules.get("datamodel")
    sys.modules["datamodel"] = shim
    try:
        spec = importlib.util.spec_from_file_location(trader_path.stem, trader_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to import trader from {trader_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            sys.modules.pop("datamodel", None)
        else:
            sys.modules["datamodel"] = previous
    return module, shim


def replay_trader(
    trader_path: Path,
    books: Dict[str, Dict[int, BookSnapshot]],
    trades: List[Dict[str, object]],
) -> Dict[str, object]:
    module, shim = load_trader_module(trader_path)
    trader = module.Trader()
    submission_qty, own_by_ts, market_by_ts = build_trade_lookup(trades)
    positions_before = positions_before_timestamp(trades)
    timestamps = sorted({timestamp for by_ts in books.values() for timestamp in by_ts})
    listings = {product: shim.Listing(product, product, XIRECS) for product in PRODUCTS}

    trader_data = ""
    replay_orders: Dict[int, List[object]] = {}
    attempted_by_key: Dict[Tuple[int, str, str, int], int] = defaultdict(int)
    attempted_class_counts: Dict[str, Counter] = defaultdict(Counter)
    filled_class_counts: Dict[str, Counter] = defaultdict(Counter)
    attempted_class_qty: Dict[str, Counter] = defaultdict(Counter)
    filled_class_qty: Dict[str, Counter] = defaultdict(Counter)

    previous_timestamp = None
    for timestamp in timestamps:
        order_depths: Dict[str, object] = {}
        for product in PRODUCTS:
            depth = shim.OrderDepth()
            snapshot = books.get(product, {}).get(timestamp)
            if snapshot is not None:
                for price, volume in zip(snapshot.bid_prices, snapshot.bid_volumes):
                    depth.buy_orders[int(price)] = int(volume)
                for price, volume in zip(snapshot.ask_prices, snapshot.ask_volumes):
                    depth.sell_orders[int(price)] = -int(volume)
            order_depths[product] = depth

        own_trades = {
            product: [
                shim.Trade(
                    symbol=product,
                    price=int(round(float(trade["price"]))),
                    quantity=int(trade["quantity"]),
                    buyer=str(trade.get("buyer", "")),
                    seller=str(trade.get("seller", "")),
                    timestamp=int(trade["timestamp"]),
                )
                for trade in own_by_ts.get(previous_timestamp or -1, {}).get(product, [])
            ]
            for product in PRODUCTS
        }
        market_trades = {
            product: [
                shim.Trade(
                    symbol=product,
                    price=int(round(float(trade["price"]))),
                    quantity=int(trade["quantity"]),
                    buyer=str(trade.get("buyer", "")),
                    seller=str(trade.get("seller", "")),
                    timestamp=int(trade["timestamp"]),
                )
                for trade in market_by_ts.get(timestamp, {}).get(product, [])
            ]
            for product in PRODUCTS
        }
        position = {product: positions_before.get(timestamp, {}).get(product, 0) for product in PRODUCTS}
        state = shim.TradingState(
            traderData=trader_data,
            timestamp=timestamp,
            listings=listings,
            order_depths=order_depths,
            own_trades=own_trades,
            market_trades=market_trades,
            position=position,
            observations=shim.Observation({}, {}),
        )

        run_output = trader.run(state)
        if not isinstance(run_output, tuple) or len(run_output) != 3:
            raise RuntimeError(f"Unexpected trader return value at {timestamp}: {run_output!r}")
        order_map, _conversions, trader_data = run_output
        replay_orders[timestamp] = []
        for product, orders in order_map.items():
            snapshot = books.get(product, {}).get(timestamp)
            if snapshot is None:
                continue
            for order in orders:
                replay_orders[timestamp].append(order)
                side = "buy" if int(order.quantity) > 0 else "sell"
                price = int(order.price)
                qty = abs(int(order.quantity))
                attempted_by_key[(timestamp, product, side, price)] += qty
                if side == "buy":
                    if snapshot.ask1 is not None and price == snapshot.ask1:
                        order_class = "take_a1"
                    elif snapshot.bid1 is not None and snapshot.ask1 is not None and snapshot.bid1 < price < snapshot.ask1:
                        order_class = "passive_inside_buy"
                    elif snapshot.bid1 is not None and price <= snapshot.bid1:
                        order_class = "passive_join_buy"
                    else:
                        order_class = "other_buy"
                else:
                    if snapshot.bid1 is not None and price == snapshot.bid1:
                        order_class = "take_b1"
                    elif snapshot.bid1 is not None and snapshot.ask1 is not None and snapshot.bid1 < price < snapshot.ask1:
                        order_class = "passive_inside_sell"
                    elif snapshot.ask1 is not None and price >= snapshot.ask1:
                        order_class = "passive_join_sell"
                    else:
                        order_class = "other_sell"
                attempted_class_counts[product][order_class] += 1
                attempted_class_qty[product][order_class] += qty
        previous_timestamp = timestamp

    for key, attempted_qty in attempted_by_key.items():
        actual_qty = submission_qty.get(key, 0)
        timestamp, product, side, price = key
        snapshot = books.get(product, {}).get(timestamp)
        if snapshot is None:
            continue
        if side == "buy":
            if snapshot.ask1 is not None and price == snapshot.ask1:
                order_class = "take_a1"
            elif snapshot.bid1 is not None and snapshot.ask1 is not None and snapshot.bid1 < price < snapshot.ask1:
                order_class = "passive_inside_buy"
            elif snapshot.bid1 is not None and price <= snapshot.bid1:
                order_class = "passive_join_buy"
            else:
                order_class = "other_buy"
        else:
            if snapshot.bid1 is not None and price == snapshot.bid1:
                order_class = "take_b1"
            elif snapshot.bid1 is not None and snapshot.ask1 is not None and snapshot.bid1 < price < snapshot.ask1:
                order_class = "passive_inside_sell"
            elif snapshot.ask1 is not None and price >= snapshot.ask1:
                order_class = "passive_join_sell"
            else:
                order_class = "other_sell"
        if actual_qty > 0:
            filled_class_counts[product][order_class] += 1
            filled_class_qty[product][order_class] += min(attempted_qty, actual_qty)

    fill_summary: Dict[str, Dict[str, Dict[str, Optional[float]]]] = {}
    for product, class_counts in sorted(attempted_class_counts.items()):
        fill_summary[product] = {}
        for order_class in sorted(class_counts):
            attempts = class_counts[order_class]
            attempt_qty = attempted_class_qty[product][order_class]
            fills = filled_class_counts[product].get(order_class, 0)
            fill_qty = filled_class_qty[product].get(order_class, 0)
            fill_summary[product][order_class] = {
                "attempt_count": attempts,
                "fill_count": fills,
                "attempt_qty": attempt_qty,
                "fill_qty": fill_qty,
                "count_fill_rate": round(fills / attempts, 4) if attempts else None,
                "qty_fill_rate": round(fill_qty / attempt_qty, 4) if attempt_qty else None,
            }
    return {
        "trader": str(trader_path),
        "fill_summary": fill_summary,
    }


def summarize_submission_trades(
    trades: List[Dict[str, object]],
    books: Dict[str, Dict[int, BookSnapshot]],
) -> Dict[str, object]:
    summary: Dict[str, object] = {}
    per_product: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    class_counts: Dict[str, Counter] = defaultdict(Counter)
    class_qty: Dict[str, Counter] = defaultdict(Counter)
    total_by_side: Dict[str, Counter] = defaultdict(Counter)

    for trade in trades:
        side = submission_side(trade)
        if side is None:
            continue
        product = str(trade["symbol"])
        timestamp = int(trade["timestamp"])
        snapshot = books.get(product, {}).get(timestamp)
        if snapshot is None:
            continue
        trade_class = classify_submission_trade(trade, snapshot)
        quantity = int(trade["quantity"])
        price = float(trade["price"])
        total_by_side[product][side] += quantity
        class_counts[product][trade_class] += 1
        class_qty[product][trade_class] += quantity

        immediate_edge = favorable_markout(side, price, snapshot.mid_price)
        if immediate_edge is not None:
            per_product[product][f"{trade_class}.immediate_edge"].append(immediate_edge)
        for horizon in HORIZONS:
            future = books.get(product, {}).get(timestamp + horizon * 100)
            future_mid = future.mid_price if future is not None else None
            markout = favorable_markout(side, price, future_mid)
            next_mid_move = favorable_next_mid_move(side, snapshot.mid_price, future_mid)
            same_side_move = favorable_same_side_level_move(side, snapshot, future)
            opp_side_move = favorable_opp_side_level_move(side, snapshot, future)
            if markout is not None:
                per_product[product][f"{trade_class}.markout_h{horizon}"].append(markout)
            if next_mid_move is not None:
                per_product[product][f"{trade_class}.next_mid_move_h{horizon}"].append(next_mid_move)
            if same_side_move is not None:
                per_product[product][f"{trade_class}.same_side_move_h{horizon}"].append(same_side_move)
            if opp_side_move is not None:
                per_product[product][f"{trade_class}.opp_side_move_h{horizon}"].append(opp_side_move)

    for product in sorted(per_product):
        product_summary = {
            "trade_counts": dict(class_counts[product]),
            "trade_qty": dict(class_qty[product]),
            "submission_qty_by_side": dict(total_by_side[product]),
            "class_metrics": {},
        }
        for key, values in sorted(per_product[product].items()):
            if "." not in key:
                continue
            trade_class, metric = key.split(".", 1)
            product_summary["class_metrics"].setdefault(trade_class, {})
            product_summary["class_metrics"][trade_class][metric] = round_or_none(mean(values))
        summary[product] = product_summary
    return summary


def summarize_external_trades(
    trades: List[Dict[str, object]],
    books: Dict[str, Dict[int, BookSnapshot]],
) -> Dict[str, object]:
    external: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    counts: Dict[str, Counter] = defaultdict(Counter)
    for trade in trades:
        if submission_side(trade) is not None:
            continue
        product = str(trade["symbol"])
        timestamp = int(trade["timestamp"])
        snapshot = books.get(product, {}).get(timestamp)
        if snapshot is None:
            continue
        side = infer_external_side(trade, snapshot)
        counts[product][side] += 1
        price = float(trade["price"])
        for horizon in HORIZONS:
            future = books.get(product, {}).get(timestamp + horizon * 100)
            future_mid = future.mid_price if future is not None else None
            markout = favorable_markout(side, price, future_mid)
            next_mid_move = favorable_next_mid_move(side, snapshot.mid_price, future_mid)
            if markout is not None:
                external[product][f"{side}.markout_h{horizon}"].append(markout)
            if next_mid_move is not None:
                external[product][f"{side}.next_mid_move_h{horizon}"].append(next_mid_move)
    summary = {}
    for product, metrics in external.items():
        product_summary = {"counts": dict(counts[product]), "metrics": {}}
        for key, values in sorted(metrics.items()):
            product_summary["metrics"][key] = round_or_none(mean(values))
        summary[product] = product_summary
    return summary


def build_trade_event_rows(
    trades: List[Dict[str, object]],
    books: Dict[str, Dict[int, BookSnapshot]],
    *,
    submission_only: bool,
) -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []
    for trade in trades:
        side = submission_side(trade)
        is_submission = side is not None
        if submission_only != is_submission:
            continue
        product = str(trade["symbol"])
        timestamp = int(trade["timestamp"])
        snapshot = books.get(product, {}).get(timestamp)
        if snapshot is None:
            continue
        if not is_submission:
            side = infer_external_side(trade, snapshot)
        trade_class = classify_submission_trade(trade, snapshot) if is_submission else "external_trade"
        row: Dict[str, object] = {
            "timestamp": timestamp,
            "day": snapshot.day,
            "product": product,
            "side": side,
            "trade_class": trade_class,
            "price": float(trade["price"]),
            "quantity": int(trade["quantity"]),
            "mid_0": snapshot.mid_price,
            "bid_1": snapshot.bid1,
            "ask_1": snapshot.ask1,
            "spread_0": snapshot.spread,
            "buyer": trade.get("buyer", ""),
            "seller": trade.get("seller", ""),
        }
        for horizon in HORIZONS:
            future = books.get(product, {}).get(timestamp + horizon * 100)
            future_mid = future.mid_price if future is not None else None
            row[f"markout_h{horizon}"] = favorable_markout(side, float(trade["price"]), future_mid)
            row[f"next_mid_move_h{horizon}"] = favorable_next_mid_move(side, snapshot.mid_price, future_mid)
            row[f"same_side_move_h{horizon}"] = favorable_same_side_level_move(side, snapshot, future)
            row[f"opp_side_move_h{horizon}"] = favorable_opp_side_level_move(side, snapshot, future)
        events.append(row)
    return events


def build_book_snapshot_rows(books: Dict[str, Dict[int, BookSnapshot]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for product, by_ts in sorted(books.items()):
        for timestamp, snapshot in sorted(by_ts.items()):
            row: Dict[str, object] = {
                "day": snapshot.day,
                "timestamp": timestamp,
                "product": product,
                "mid_price": snapshot.mid_price,
                "profit_and_loss": snapshot.profit_and_loss,
            }
            for level in range(3):
                row[f"bid_price_{level + 1}"] = snapshot.level("bid", level)
                row[f"bid_volume_{level + 1}"] = snapshot.bid_volumes[level] if level < len(snapshot.bid_volumes) else None
                row[f"ask_price_{level + 1}"] = snapshot.level("ask", level)
                row[f"ask_volume_{level + 1}"] = snapshot.ask_volumes[level] if level < len(snapshot.ask_volumes) else None
            rows.append(row)
    return rows


def write_rows(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        path.write_text("")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_exports(export_dir: Path, summary: Dict[str, object], books: Dict[str, Dict[int, BookSnapshot]], trades: List[Dict[str, object]]) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    label = str(summary["label"])
    (export_dir / f"{label}_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    write_rows(export_dir / f"{label}_book_snapshots.csv", build_book_snapshot_rows(books))
    write_rows(
        export_dir / f"{label}_submission_trade_events.csv",
        build_trade_event_rows(trades, books, submission_only=True),
    )
    write_rows(
        export_dir / f"{label}_external_trade_events.csv",
        build_trade_event_rows(trades, books, submission_only=False),
    )


def build_run_comparison(summaries: List[Dict[str, object]]) -> List[Dict[str, object]]:
    if len(summaries) < 2:
        return []
    baseline = summaries[0]
    baseline_profit = baseline.get("profit")
    baseline_products = baseline.get("final_product_pnl", {})
    rows: List[Dict[str, object]] = []
    for summary in summaries[1:]:
        row: Dict[str, object] = {
            "baseline": baseline["label"],
            "candidate": summary["label"],
            "profit": summary.get("profit"),
            "profit_delta": None,
        }
        if isinstance(summary.get("profit"), (int, float)) and isinstance(baseline_profit, (int, float)):
            row["profit_delta"] = round(float(summary["profit"]) - float(baseline_profit), 3)
        candidate_products = summary.get("final_product_pnl", {})
        for product in PRODUCTS:
            candidate_value = candidate_products.get(product)
            baseline_value = baseline_products.get(product)
            row[f"{product}_pnl"] = candidate_value
            if isinstance(candidate_value, (int, float)) and isinstance(baseline_value, (int, float)):
                row[f"{product}_delta"] = round(float(candidate_value) - float(baseline_value), 3)
            else:
                row[f"{product}_delta"] = None
        rows.append(row)
    return rows


def print_comparison_table(rows: List[Dict[str, object]]) -> None:
    if not rows:
        return
    print("Comparison vs first run:")
    for row in rows:
        print(
            f"  {row['candidate']} vs {row['baseline']}:"
            f" profit_delta={row['profit_delta']}"
            f" ash_delta={row.get('ASH_COATED_OSMIUM_delta')}"
            f" pepper_delta={row.get('INTARIAN_PEPPER_ROOT_delta')}"
        )


def build_run_summary(path: Path, replay_trader_path: Optional[Path]) -> Dict[str, object]:
    payload = load_payload(path)
    books = parse_activities_log(str(payload.get("activitiesLog", "")))
    trades = list(payload.get("tradeHistory", []))
    final_pnl = product_final_pnl(books)
    run_summary: Dict[str, object] = {
        "label": infer_run_label(path),
        "source": str(path),
        "profit": payload.get("profit"),
        "status": payload.get("status"),
        "positions": payload.get("positions", []),
        "graph": parse_graph_log(str(payload.get("graphLog", ""))),
        "final_product_pnl": final_pnl,
        "submission_trade_summary": summarize_submission_trades(trades, books),
        "external_trade_summary": summarize_external_trades(trades, books),
        "_books": books,
        "_trades": trades,
    }
    if replay_trader_path is not None:
        run_summary["replay"] = replay_trader(replay_trader_path, books, trades)
    return run_summary


def print_run_summary(summary: Dict[str, object]) -> None:
    print(f"Run: {summary['label']}")
    print(f"  source: {summary['source']}")
    if summary.get("profit") is not None:
        print(f"  official profit: {summary['profit']}")
    if summary.get("status") is not None:
        print(f"  status: {summary['status']}")
    if summary.get("final_product_pnl"):
        print(f"  final product pnl: {summary['final_product_pnl']}")
    print("  submission trade summary:")
    for product, product_summary in summary["submission_trade_summary"].items():
        print(f"    {product}")
        print(f"      qty by side: {product_summary['submission_qty_by_side']}")
        for trade_class, count in product_summary["trade_counts"].items():
            qty = product_summary["trade_qty"].get(trade_class, 0)
            metrics = product_summary["class_metrics"].get(trade_class, {})
            markout10 = metrics.get("markout_h10")
            next_mid10 = metrics.get("next_mid_move_h10")
            print(
                f"      {trade_class}: n={count} qty={qty}"
                f" markout_h10={markout10} next_mid_h10={next_mid10}"
            )
    if summary.get("external_trade_summary"):
        print("  external trade summary:")
        for product, product_summary in summary["external_trade_summary"].items():
            print(f"    {product}: counts={product_summary['counts']}")
            for key, value in product_summary["metrics"].items():
                if key.endswith("markout_h10") or key.endswith("next_mid_move_h10"):
                    print(f"      {key}: {value}")
    if summary.get("replay"):
        print("  replay / intended-order fill summary:")
        for product, product_fill in summary["replay"]["fill_summary"].items():
            print(f"    {product}")
            for order_class, fill_info in product_fill.items():
                print(
                    f"      {order_class}: attempts={fill_info['attempt_count']}"
                    f" fills={fill_info['fill_count']}"
                    f" qty_fill_rate={fill_info['qty_fill_rate']}"
                )


def public_summary(summary: Dict[str, object]) -> Dict[str, object]:
    return {key: value for key, value in summary.items() if not key.startswith("_")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", nargs="+", help="Official log bundles (.zip), payload files, or directories")
    parser.add_argument(
        "--replay-trader",
        type=Path,
        help="Replay this local trader file against the official activity snapshots and compare intended orders to actual fills",
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        help="Write per-run JSON summaries plus normalized CSV exports for books and trade events",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    run_paths = discover_input_paths(Path(path) for path in args.runs)
    summaries = [build_run_summary(path, args.replay_trader) for path in run_paths]
    if args.export_dir is not None:
        args.export_dir.mkdir(parents=True, exist_ok=True)
        for summary in summaries:
            write_exports(args.export_dir, public_summary(summary), summary["_books"], summary["_trades"])
        comparison_rows = build_run_comparison([public_summary(summary) for summary in summaries])
        if comparison_rows:
            write_rows(args.export_dir / "run_comparison.csv", comparison_rows)
    if args.json:
        print(json.dumps([public_summary(summary) for summary in summaries], indent=2, sort_keys=True))
        return
    for summary in summaries:
        print_run_summary(summary)
        print()
    print_comparison_table(build_run_comparison([public_summary(summary) for summary in summaries]))


if __name__ == "__main__":
    main()
