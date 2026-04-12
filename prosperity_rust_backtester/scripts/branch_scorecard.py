#!/usr/bin/env python3
import argparse
import glob
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def product_book(row: Dict[str, object], product: str) -> Tuple[int, int, float]:
    book = row["products"][product]  # type: ignore[index]
    bids = book.get("bids") or []  # type: ignore[union-attr]
    asks = book.get("asks") or []  # type: ignore[union-attr]
    best_bid = int(bids[0]["price"]) if bids else 0
    best_ask = int(asks[0]["price"]) if asks else 0
    mid = float(book.get("mid_price", (best_bid + best_ask) / 2.0 if best_bid and best_ask else 0.0))  # type: ignore[union-attr]
    return best_bid, best_ask, mid


def classify_fill(row: Dict[str, object], trade: Dict[str, object]) -> str:
    product = str(trade["symbol"])
    best_bid, best_ask, _ = product_book(row, product)
    price = int(trade["price"])
    if trade.get("buyer") == "SUBMISSION":
        return "aggressive" if best_ask and price >= best_ask else "passive"
    return "aggressive" if best_bid and price <= best_bid else "passive"


def drawdown(values: List[float]) -> float:
    peak = values[0] if values else 0.0
    max_dd = 0.0
    for value in values:
        peak = max(peak, value)
        max_dd = max(max_dd, peak - value)
    return max_dd


def future_edge(rows: List[Dict[str, object]], product: str, horizon: int) -> Tuple[int, float]:
    total = 0.0
    n = 0
    for i, row in enumerate(rows[:-horizon]):
        future_mid = product_book(rows[i + horizon], product)[2]
        for trade in row["own_trades"]:  # type: ignore[index]
            if trade["symbol"] != product:
                continue
            side = 1 if trade.get("buyer") == "SUBMISSION" else -1
            total += (future_mid - int(trade["price"])) * side * int(trade["quantity"])
            n += 1
    return n, total / n if n else 0.0


def summarize_bundle(path: Path) -> Dict[str, Dict[str, object]]:
    data = json.loads(path.read_text())
    rows = data.get("timeline", [])
    products = data.get("products", [])
    out: Dict[str, Dict[str, object]] = {}
    for product in products:
        positions = [int(row.get("position", {}).get(product, 0)) for row in rows]
        pnls = [float(row.get("pnl_by_product", {}).get(product, 0.0)) for row in rows]
        fills = []
        fill_events = Counter()
        fill_units = Counter()
        for row in rows:
            for trade in row.get("own_trades", []):
                if trade.get("symbol") != product:
                    continue
                fills.append(trade)
                kind = classify_fill(row, trade)
                side = "buy" if trade.get("buyer") == "SUBMISSION" else "sell"
                qty = int(trade["quantity"])
                fill_events[f"{kind}_{side}"] += 1
                fill_units[f"{kind}_{side}"] += qty
        edge5 = future_edge(rows, product, 5)
        edge20 = future_edge(rows, product, 20)
        out[product] = {
            "fills": len(fills),
            "units": sum(int(t["quantity"]) for t in fills),
            "pos_min": min(positions) if positions else 0,
            "pos_max": max(positions) if positions else 0,
            "pos_final": positions[-1] if positions else 0,
            "avg_abs_pos": round(sum(abs(x) for x in positions) / len(positions), 2) if positions else 0.0,
            "near60": sum(1 for x in positions if abs(x) >= 60),
            "drawdown": round(drawdown(pnls), 2),
            "edge5_avg": round(edge5[1], 3),
            "edge20_avg": round(edge20[1], 3),
            "fill_events": dict(fill_events),
            "fill_units": dict(fill_units),
        }
    return out


def summarize_run(run_dir: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for metrics_path in sorted(run_dir.glob("*metrics.json")):
        stem = metrics_path.name[: -len("-metrics.json")]
        metrics = json.loads(metrics_path.read_text())
        bundle_path = run_dir / f"{stem}-bundle.json"
        bundle = summarize_bundle(bundle_path) if bundle_path.exists() else {}
        row: Dict[str, object] = {
            "run": run_dir.name,
            "set": stem,
            "trader": metrics.get("trader_path", ""),
            "total": metrics.get("final_pnl_total", 0.0),
            "own_trades": metrics.get("own_trade_count", 0),
        }
        for product, pnl in metrics.get("final_pnl_by_product", {}).items():
            row[f"{product}_pnl"] = pnl
            for key, value in bundle.get(product, {}).items():
                if key in ("fill_events", "fill_units"):
                    continue
                row[f"{product}_{key}"] = value
        rows.append(row)
    return rows


def fmt(value: object) -> str:
    if isinstance(value, float):
        if math.isfinite(value):
            return f"{value:.2f}"
        return "nan"
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", nargs="+", help="Run ids or run directories")
    parser.add_argument("--runs-root", default="runs")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    all_rows: List[Dict[str, object]] = []
    for run in args.runs:
        path = Path(run)
        if not path.exists():
            path = Path(args.runs_root) / run
        all_rows.extend(summarize_run(path))

    if args.json:
        print(json.dumps(all_rows, indent=2, sort_keys=True))
        return

    columns = [
        "run",
        "set",
        "total",
        "EMERALDS_pnl",
        "TOMATOES_pnl",
        "own_trades",
        "TOMATOES_pos_min",
        "TOMATOES_pos_max",
        "TOMATOES_pos_final",
        "TOMATOES_avg_abs_pos",
        "TOMATOES_near60",
        "TOMATOES_drawdown",
        "TOMATOES_edge5_avg",
    ]
    print(",".join(columns))
    for row in all_rows:
        print(",".join(fmt(row.get(col, "")) for col in columns))


if __name__ == "__main__":
    main()
