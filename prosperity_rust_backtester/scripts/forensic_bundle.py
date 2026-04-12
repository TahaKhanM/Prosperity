#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from typing import Dict, List, Tuple


def product_book(row: Dict[str, object], product: str) -> Tuple[int, int, float]:
    book = row["products"][product]  # type: ignore[index]
    bids = book["bids"]  # type: ignore[index]
    asks = book["asks"]  # type: ignore[index]
    best_bid = int(bids[0]["price"]) if bids else 0
    best_ask = int(asks[0]["price"]) if asks else 0
    mid = float(book["mid_price"]) if book.get("mid_price") is not None else 0.0
    return best_bid, best_ask, mid


def classify_fill(row: Dict[str, object], trade: Dict[str, object]) -> str:
    product = str(trade["symbol"])
    best_bid, best_ask, _ = product_book(row, product)
    price = int(trade["price"])
    if trade.get("buyer") == "SUBMISSION":
        return "aggressive" if best_ask and price >= best_ask else "passive"
    return "aggressive" if best_bid and price <= best_bid else "passive"


def max_drawdown(values: List[float]) -> float:
    peak = values[0] if values else 0.0
    drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        drawdown = max(drawdown, peak - value)
    return drawdown


def signed_future_edge(rows: List[Dict[str, object]], product: str, horizon: int) -> Tuple[int, float, float]:
    vals: List[float] = []
    for i, row in enumerate(rows[:-horizon]):
        future_mid = product_book(rows[i + horizon], product)[2]
        for trade in row["own_trades"]:  # type: ignore[index]
            if trade["symbol"] != product:
                continue
            side = 1 if trade.get("buyer") == "SUBMISSION" else -1
            vals.append((future_mid - int(trade["price"])) * side * int(trade["quantity"]))
    if not vals:
        return 0, 0.0, 0.0
    return len(vals), sum(vals), sum(vals) / len(vals)


def missed_future_edge(rows: List[Dict[str, object]], product: str, horizon: int) -> Tuple[int, int]:
    missed_buys = 0
    missed_sells = 0
    for i, row in enumerate(rows[:-horizon]):
        _, _, future_mid = product_book(rows[i + horizon], product)
        best_bid, best_ask, _ = product_book(row, product)
        order_prices = {
            (order["price"], 1 if order["quantity"] > 0 else -1)
            for order in row["orders"]  # type: ignore[index]
            if order["symbol"] == product
        }
        if best_ask and future_mid - best_ask >= 2 and (best_ask, 1) not in order_prices:
            missed_buys += 1
        if best_bid and best_bid - future_mid >= 2 and (best_bid, -1) not in order_prices:
            missed_sells += 1
    return missed_buys, missed_sells


def summarize(path: str) -> None:
    with open(path) as f:
        bundle = json.load(f)
    rows = bundle["timeline"]
    print(f"\n{path}")
    print(f"ticks={len(rows)} total={rows[-1]['pnl_total']:.2f}")
    for product in bundle["products"]:
        positions = [int(row["position"].get(product, 0)) for row in rows]
        pnls = [float(row["pnl_by_product"].get(product, 0.0)) for row in rows]
        fills = []
        fill_kind = Counter()
        fill_units = Counter()
        for row in rows:
            for trade in row["own_trades"]:
                if trade["symbol"] != product:
                    continue
                kind = classify_fill(row, trade)
                side = "buy" if trade.get("buyer") == "SUBMISSION" else "sell"
                qty = int(trade["quantity"])
                fills.append(trade)
                fill_kind[(kind, side)] += 1
                fill_units[(kind, side)] += qty
        edge5 = signed_future_edge(rows, product, 5)
        edge20 = signed_future_edge(rows, product, 20)
        missed5 = missed_future_edge(rows, product, 5)
        avg_abs = sum(abs(x) for x in positions) / len(positions)
        near60 = sum(1 for x in positions if abs(x) >= 60)
        print(
            f"{product}: pnl={pnls[-1]:.2f} fills={len(fills)} units={sum(int(t['quantity']) for t in fills)} "
            f"pos=[{min(positions)},{max(positions)}] final={positions[-1]} avg_abs={avg_abs:.1f} "
            f"near60={near60} dd={max_drawdown(pnls):.1f}"
        )
        print(f"  fill_events={dict(fill_kind)}")
        print(f"  fill_units={dict(fill_units)}")
        print(f"  future_edge_h5=(n={edge5[0]},sum={edge5[1]:.1f},avg={edge5[2]:.2f})")
        print(f"  future_edge_h20=(n={edge20[0]},sum={edge20[1]:.1f},avg={edge20[2]:.2f})")
        print(f"  missed_future_edge_h5=buy:{missed5[0]} sell:{missed5[1]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundles", nargs="+")
    args = parser.parse_args()
    for path in args.bundles:
        summarize(path)


if __name__ == "__main__":
    main()
