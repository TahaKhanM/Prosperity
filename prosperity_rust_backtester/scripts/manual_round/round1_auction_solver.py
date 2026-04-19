#!/usr/bin/env python3
"""Simulate Round 1 auction final orders against a frozen order book."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from workflow_common import RESEARCH_ROOT, ensure_directory, ensure_path, timestamp_slug, write_csv


@dataclass(frozen=True)
class AuctionOrder:
    side: str
    price: int
    quantity: int
    owner: str
    timestamp: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, help="JSON scenario file describing the frozen book.")
    parser.add_argument("--price-min", type=int, required=True, help="Minimum candidate price to simulate.")
    parser.add_argument("--price-max", type=int, required=True, help="Maximum candidate price to simulate.")
    parser.add_argument("--quantity-min", type=int, required=True, help="Minimum candidate quantity to simulate.")
    parser.add_argument("--quantity-max", type=int, required=True, help="Maximum candidate quantity to simulate.")
    parser.add_argument("--quantity-step", type=int, default=1, help="Quantity step for the grid.")
    parser.add_argument(
        "--side",
        choices=("buy", "sell", "both"),
        default="both",
        help="Which final-order side(s) to simulate.",
    )
    parser.add_argument("--run-id", help="Optional output folder id.")
    return parser.parse_args()


def normalize_orders(payload: dict) -> tuple[list[AuctionOrder], dict]:
    orders: list[AuctionOrder] = []
    timestamp = 0
    if payload.get("orders"):
        for raw in payload["orders"]:
            orders.append(
                AuctionOrder(
                    side=str(raw["side"]).lower(),
                    price=int(raw["price"]),
                    quantity=int(raw["quantity"]),
                    owner=str(raw.get("owner", "book")),
                    timestamp=int(raw.get("timestamp", timestamp)),
                )
            )
            timestamp += 1
    else:
        for raw in payload.get("bids", []):
            orders.append(
                AuctionOrder(
                    side="buy",
                    price=int(raw["price"]),
                    quantity=int(raw["quantity"]),
                    owner=str(raw.get("owner", "book")),
                    timestamp=int(raw.get("timestamp", timestamp)),
                )
            )
            timestamp += 1
        for raw in payload.get("asks", []):
            orders.append(
                AuctionOrder(
                    side="sell",
                    price=int(raw["price"]),
                    quantity=int(raw["quantity"]),
                    owner=str(raw.get("owner", "book")),
                    timestamp=int(raw.get("timestamp", timestamp)),
                )
            )
            timestamp += 1

    if not orders:
        raise SystemExit("scenario must provide at least one bid or ask")
    metadata = {
        "product": payload.get("product", "unknown_product"),
        "terminal_value": float(payload.get("terminal_value", 0.0)),
        "fee_per_unit": float(payload.get("fee_per_unit", 0.0)),
        "initial_inventory": int(payload.get("initial_inventory", 0)),
    }
    return orders, metadata


def traded_volume(orders: list[AuctionOrder], price: int) -> int:
    demand = sum(order.quantity for order in orders if order.side == "buy" and order.price >= price)
    supply = sum(order.quantity for order in orders if order.side == "sell" and order.price <= price)
    return min(demand, supply)


def clearing_price(orders: list[AuctionOrder]) -> tuple[int, int]:
    prices = sorted({order.price for order in orders})
    ranked = [(traded_volume(orders, price), price) for price in prices]
    volume, price = max(ranked, key=lambda item: (item[0], item[1]))
    return price, volume


def fill_allocations(orders: list[AuctionOrder], clear_price: int, clear_volume: int) -> dict[tuple[str, str], int]:
    allocations: dict[tuple[str, str], int] = {}
    remaining = clear_volume
    buy_orders = sorted(
        [order for order in orders if order.side == "buy" and order.price >= clear_price],
        key=lambda order: (-order.price, order.timestamp),
    )
    for order in buy_orders:
        if remaining <= 0:
            break
        fill = min(order.quantity, remaining)
        allocations[(order.owner, f"buy:{order.price}:{order.timestamp}")] = fill
        remaining -= fill

    remaining = clear_volume
    sell_orders = sorted(
        [order for order in orders if order.side == "sell" and order.price <= clear_price],
        key=lambda order: (order.price, order.timestamp),
    )
    for order in sell_orders:
        if remaining <= 0:
            break
        fill = min(order.quantity, remaining)
        allocations[(order.owner, f"sell:{order.price}:{order.timestamp}")] = fill
        remaining -= fill
    return allocations


def evaluate_candidate(
    book_orders: list[AuctionOrder],
    metadata: dict,
    candidate_side: str,
    candidate_price: int,
    candidate_quantity: int,
) -> dict[str, object]:
    candidate_order = AuctionOrder(
        side=candidate_side,
        price=candidate_price,
        quantity=candidate_quantity,
        owner="candidate",
        timestamp=max(order.timestamp for order in book_orders) + 1,
    )
    orders = [*book_orders, candidate_order]
    clear_price, clear_volume = clearing_price(orders)
    fills = fill_allocations(orders, clear_price, clear_volume)
    fill_key = (candidate_order.owner, f"{candidate_order.side}:{candidate_order.price}:{candidate_order.timestamp}")
    filled_quantity = int(fills.get(fill_key, 0))

    buy_fill = filled_quantity if candidate_side == "buy" else 0
    sell_fill = filled_quantity if candidate_side == "sell" else 0
    net_cash = (sell_fill - buy_fill) * clear_price
    fees = (buy_fill + sell_fill) * float(metadata["fee_per_unit"])
    final_inventory = int(metadata["initial_inventory"]) + buy_fill - sell_fill
    payoff = net_cash + final_inventory * float(metadata["terminal_value"]) - fees

    return {
        "side": candidate_side,
        "price": candidate_price,
        "quantity": candidate_quantity,
        "clear_price": clear_price,
        "clear_volume": clear_volume,
        "filled_quantity": filled_quantity,
        "net_cash": round(net_cash, 4),
        "final_inventory": final_inventory,
        "fees": round(fees, 4),
        "payoff": round(payoff, 4),
    }


def build_recommendations(rows: list[dict[str, object]], metadata: dict) -> str:
    top_rows = sorted(rows, key=lambda row: float(row["payoff"]), reverse=True)[:10]
    lines = [
        "# Best Order Recommendations",
        "",
        f"- Product: `{metadata['product']}`",
        f"- Terminal value: `{metadata['terminal_value']}`",
        f"- Fee per unit: `{metadata['fee_per_unit']}`",
        f"- Initial inventory assumption: `{metadata['initial_inventory']}`",
        "",
        "## Top Grid Points",
        "",
    ]
    for row in top_rows:
        lines.append(
            f"- `{row['side']}` `{row['quantity']}` @ `{row['price']}` -> payoff `{row['payoff']}`, "
            f"clear `{row['clear_price']}` with fill `{row['filled_quantity']}`"
        )
    return "\n".join(lines) + "\n"


def build_sensitivity_notes(rows: list[dict[str, object]]) -> str:
    rows = sorted(rows, key=lambda row: float(row["payoff"]), reverse=True)
    best = rows[0]
    near_best = [row for row in rows if float(row["payoff"]) >= float(best["payoff"]) * 0.95]
    same_clear = [row for row in near_best if row["clear_price"] == best["clear_price"]]
    lines = [
        "# Sensitivity Notes",
        "",
        f"- Best payoff: `{best['payoff']}` from `{best['side']}` `{best['quantity']}` @ `{best['price']}`.",
        f"- Grid points within 95% of best payoff: `{len(near_best)}`.",
        f"- Of those near-best points, `{len(same_clear)}` share the best clearing price `{best['clear_price']}`.",
        "- If only a few nearby points remain near-best, the recommendation is price/size sensitive.",
        "- If many nearby points share the same clearing price and payoff band, the choice sits in a stable basin.",
        "- This solver assumes the documented volume-first, higher-price-tiebreak clearing rule and marks final inventory to the terminal value.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    scenario_path = ensure_path(args.scenario, base=RESEARCH_ROOT.parent)
    payload = json.loads(scenario_path.read_text(encoding="utf-8"))
    book_orders, metadata = normalize_orders(payload)

    run_id = args.run_id or f"{timestamp_slug()}_{metadata['product']}"
    output_dir = ensure_directory(RESEARCH_ROOT / "07_manual_round" / "round1_auction" / run_id)

    rows = []
    sides = ("buy", "sell") if args.side == "both" else (args.side,)
    for side in sides:
        for price in range(args.price_min, args.price_max + 1):
            for quantity in range(args.quantity_min, args.quantity_max + 1, args.quantity_step):
                rows.append(evaluate_candidate(book_orders, metadata, side, price, quantity))

    rows.sort(key=lambda row: (float(row["payoff"]), int(row["filled_quantity"])), reverse=True)
    write_csv(
        output_dir / "payoff_grid.csv",
        ["side", "price", "quantity", "clear_price", "clear_volume", "filled_quantity", "net_cash", "final_inventory", "fees", "payoff"],
        rows,
    )
    (output_dir / "best_order_recommendations.md").write_text(
        build_recommendations(rows, metadata),
        encoding="utf-8",
    )
    (output_dir / "sensitivity_notes.md").write_text(build_sensitivity_notes(rows), encoding="utf-8")

    print(f"output_dir: {output_dir.relative_to(RESEARCH_ROOT.parent)}")
    print(f"payoff_grid: {(output_dir / 'payoff_grid.csv').relative_to(RESEARCH_ROOT.parent)}")
    print(f"recommendations: {(output_dir / 'best_order_recommendations.md').relative_to(RESEARCH_ROOT.parent)}")


if __name__ == "__main__":
    main()
