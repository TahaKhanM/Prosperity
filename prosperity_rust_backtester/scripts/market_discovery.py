#!/usr/bin/env python3
import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


Row = Dict[str, float]


def as_float(value: object) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def corr(xs: List[float], ys: List[float]) -> float:
    if len(xs) < 3 or len(xs) != len(ys):
        return 0.0
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return 0.0
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return cov / math.sqrt(vx * vy)


def load_price_csv(path: Path, source: str) -> Dict[str, List[Row]]:
    out: Dict[str, List[Row]] = defaultdict(list)
    with path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for raw in reader:
            product = str(raw["product"])
            bid = as_float(raw.get("bid_price_1"))
            ask = as_float(raw.get("ask_price_1"))
            if bid is None or ask is None:
                continue
            bid_vol = abs(as_float(raw.get("bid_volume_1")) or 0.0)
            ask_vol = abs(as_float(raw.get("ask_volume_1")) or 0.0)
            total = bid_vol + ask_vol
            mid = as_float(raw.get("mid_price"))
            if mid is None:
                mid = (bid + ask) / 2.0
            micro = (bid * ask_vol + ask * bid_vol) / total if total > 0 else mid
            imbalance = (bid_vol - ask_vol) / total if total > 0 else 0.0
            out[product].append(
                {
                    "source_id": float(hash(source) % 10_000_000),
                    "day": as_float(raw.get("day")) or 0.0,
                    "timestamp": as_float(raw.get("timestamp")) or 0.0,
                    "bid": bid,
                    "ask": ask,
                    "spread": ask - bid,
                    "mid": mid,
                    "micro_delta": micro - mid,
                    "imbalance": imbalance,
                    "bid_vol": bid_vol,
                    "ask_vol": ask_vol,
                    "trade_count": 0.0,
                    "trade_qty": 0.0,
                    "trade_signed_edge": 0.0,
                }
            )
    return out


def load_submission_json(path: Path) -> Dict[str, List[Row]]:
    out: Dict[str, List[Row]] = defaultdict(list)
    if not path.exists():
        return out
    data = json.loads(path.read_text())
    for tick in data.get("ticks", []):
        for product, book in tick.get("products", {}).items():
            bids = book.get("bids") or []
            asks = book.get("asks") or []
            if not bids or not asks:
                continue
            bid = float(bids[0]["price"])
            ask = float(asks[0]["price"])
            bid_vol = abs(float(bids[0].get("volume", 0)))
            ask_vol = abs(float(asks[0].get("volume", 0)))
            total = bid_vol + ask_vol
            mid = float(book.get("mid_price", (bid + ask) / 2.0))
            micro = (bid * ask_vol + ask * bid_vol) / total if total > 0 else mid
            imbalance = (bid_vol - ask_vol) / total if total > 0 else 0.0
            out[product].append(
                {
                    "source_id": 99_999.0,
                    "day": float(tick.get("day", -1)),
                    "timestamp": float(tick.get("timestamp", 0)),
                    "bid": bid,
                    "ask": ask,
                    "spread": ask - bid,
                    "mid": mid,
                    "micro_delta": micro - mid,
                    "imbalance": imbalance,
                    "bid_vol": bid_vol,
                    "ask_vol": ask_vol,
                    "trade_count": 0.0,
                    "trade_qty": 0.0,
                    "trade_signed_edge": 0.0,
                }
            )
    return out


def merge_books(book_sets: Iterable[Dict[str, List[Row]]]) -> Dict[str, List[Row]]:
    merged: Dict[str, List[Row]] = defaultdict(list)
    for books in book_sets:
        for product, rows in books.items():
            merged[product].extend(rows)
    for rows in merged.values():
        rows.sort(key=lambda r: (r["source_id"], r["day"], r["timestamp"]))
    return merged


def load_trades(path: Path, price_rows: Dict[str, List[Row]]) -> None:
    if not path.exists():
        return
    row_by_key: Dict[Tuple[str, int, int], Row] = {}
    for product, rows in price_rows.items():
        for row in rows:
            row_by_key[(product, int(row["day"]), int(row["timestamp"]))] = row
    with path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for trade in reader:
            product = str(trade["symbol"])
            timestamp = int(float(trade["timestamp"]))
            qty = abs(float(trade["quantity"]))
            price = float(trade["price"])
            candidates = [k for k in row_by_key if k[0] == product and k[2] == timestamp]
            for key in candidates:
                row = row_by_key[key]
                row["trade_count"] += 1.0
                row["trade_qty"] += qty
                row["trade_signed_edge"] += (row["mid"] - price) * qty


def percentile(vals: List[float], pct: float) -> float:
    if not vals:
        return 0.0
    vals = sorted(vals)
    idx = min(len(vals) - 1, max(0, int(round((len(vals) - 1) * pct))))
    return vals[idx]


def summarize_product(product: str, rows: List[Row], horizons: List[int]) -> Dict[str, object]:
    mids = [r["mid"] for r in rows]
    spreads = [r["spread"] for r in rows]
    out: Dict[str, object] = {
        "ticks": len(rows),
        "mid_mean": round(sum(mids) / len(mids), 4) if mids else 0.0,
        "mid_std": round(math.sqrt(sum((x - sum(mids) / len(mids)) ** 2 for x in mids) / len(mids)), 4) if mids else 0.0,
        "mid_min": min(mids) if mids else 0.0,
        "mid_max": max(mids) if mids else 0.0,
        "spread_counts": dict(Counter(spreads).most_common(8)),
        "spread_mean": round(sum(spreads) / len(spreads), 4) if spreads else 0.0,
        "imbalance_mean": round(sum(r["imbalance"] for r in rows) / len(rows), 4) if rows else 0.0,
        "micro_delta_std": round(math.sqrt(sum(r["micro_delta"] ** 2 for r in rows) / len(rows)), 4) if rows else 0.0,
        "trade_count": int(sum(r["trade_count"] for r in rows)),
        "trade_qty": int(sum(r["trade_qty"] for r in rows)),
    }

    if len(rows) >= 3:
        ret1 = [0.0]
        for i in range(1, len(rows)):
            same_stream = rows[i]["source_id"] == rows[i - 1]["source_id"] and rows[i]["day"] == rows[i - 1]["day"]
            ret1.append(rows[i]["mid"] - rows[i - 1]["mid"] if same_stream else 0.0)
        z20 = []
        for i, row in enumerate(rows):
            start = max(0, i - 19)
            window = [
                rows[j]["mid"]
                for j in range(start, i + 1)
                if rows[j]["source_id"] == row["source_id"] and rows[j]["day"] == row["day"]
            ]
            avg = sum(window) / len(window)
            z20.append(row["mid"] - avg)
        out["ret1_abs_p50"] = round(percentile([abs(x) for x in ret1], 0.5), 4)
        out["ret1_abs_p95"] = round(percentile([abs(x) for x in ret1], 0.95), 4)

        correlations: Dict[str, Dict[str, float]] = {}
        opportunities: Dict[str, Dict[str, int]] = {}
        for h in horizons:
            features: Dict[str, List[float]] = defaultdict(list)
            future: List[float] = []
            opp = Counter()
            for i, row in enumerate(rows[:-h]):
                nxt = rows[i + h]
                if nxt["source_id"] != row["source_id"] or nxt["day"] != row["day"]:
                    continue
                change = nxt["mid"] - row["mid"]
                future.append(change)
                features["micro_delta"].append(row["micro_delta"])
                features["imbalance"].append(row["imbalance"])
                features["ret1"].append(ret1[i])
                features["z20"].append(z20[i])
                features["spread"].append(row["spread"])
                for threshold in (1.0, 2.0, 4.0):
                    if nxt["mid"] - row["ask"] >= threshold:
                        opp[f"take_buy_ge_{threshold:g}"] += 1
                    if row["bid"] - nxt["mid"] >= threshold:
                        opp[f"take_sell_ge_{threshold:g}"] += 1
                    inside_bid = row["bid"] + 1
                    inside_ask = row["ask"] - 1
                    if inside_bid < row["ask"] and nxt["mid"] - inside_bid >= threshold:
                        opp[f"inside_buy_ge_{threshold:g}"] += 1
                    if inside_ask > row["bid"] and inside_ask - nxt["mid"] >= threshold:
                        opp[f"inside_sell_ge_{threshold:g}"] += 1
            correlations[f"h{h}"] = {k: round(corr(v, future), 4) for k, v in features.items()}
            opportunities[f"h{h}"] = dict(opp)
        out["future_correlations"] = correlations
        out["quote_opportunities"] = opportunities
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="datasets/tutorial")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.dataset)
    price_sets = [load_price_csv(p, p.name) for p in sorted(root.glob("prices_*.csv"))]
    merged = merge_books(price_sets + [load_submission_json(root / "submission.json")])
    for trade_path in sorted(root.glob("trades_*.csv")):
        load_trades(trade_path, merged)

    report = {product: summarize_product(product, rows, [1, 5, 20]) for product, rows in sorted(merged.items())}
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print(f"Market discovery: {root}")
    for product, summary in report.items():
        print(f"\n{product}")
        for key, value in summary.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
