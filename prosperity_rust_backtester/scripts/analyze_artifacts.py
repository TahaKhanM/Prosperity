#!/usr/bin/env python3
import argparse
import collections
import json
import os
from typing import Dict, Iterable, Tuple


def side(trade: Dict[str, object]) -> str:
    return "BUY" if trade.get("buyer") == "SUBMISSION" else "SELL"


def summarize_bundle(path: str) -> None:
    with open(path) as f:
        bundle = json.load(f)

    timeline = bundle["timeline"]
    print(f"\n{path}")
    print(f"ticks={len(timeline)} final_pnl={timeline[-1]['pnl_total']:.2f}")

    products = bundle.get("products") or sorted(timeline[-1]["pnl_by_product"])
    for product in products:
        fills = []
        positions = []
        order_counts = collections.Counter()
        market_counts = collections.Counter()
        for row in timeline:
            positions.append(int(row["position"].get(product, 0)))
            for order in row["orders"]:
                if order["symbol"] == product:
                    order_side = "BUY" if order["quantity"] > 0 else "SELL"
                    order_counts[(order_side, int(order["price"]))] += 1
            for trade in row["own_trades"]:
                if trade["symbol"] == product:
                    fills.append((side(trade), int(trade["price"]), int(trade["quantity"])))
            for trade in row["market_trades"]:
                if trade["symbol"] == product:
                    market_counts[int(trade["price"])] += int(trade["quantity"])

        fill_qty = collections.Counter()
        fill_events = collections.Counter()
        for fill_side, price, qty in fills:
            fill_events[(fill_side, price)] += 1
            fill_qty[(fill_side, price)] += qty

        pnl = timeline[-1]["pnl_by_product"].get(product, 0.0)
        print(
            f"{product}: pnl={pnl:.2f} fills={len(fills)} units={sum(q for _, _, q in fills)} "
            f"pos_min={min(positions)} pos_max={max(positions)} final_pos={positions[-1]}"
        )
        print(f"  fill_units_top={fill_qty.most_common(10)}")
        print(f"  fill_events_top={fill_events.most_common(10)}")
        print(f"  order_price_top={order_counts.most_common(10)}")
        print(f"  market_qty_price_top={market_counts.most_common(10)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundles", nargs="+", help="bundle.json files to inspect")
    args = parser.parse_args()
    for path in args.bundles:
        summarize_bundle(path)


if __name__ == "__main__":
    main()
