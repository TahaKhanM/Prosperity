"""Counterparty / bot-name alpha scanner.

Past Prosperity winners (notably `Olivia` in P3) planted named bots that
consistently bought at daily lows and sold at daily highs. Detecting these
counterparties early is historically the single highest-alpha move.

This script ingests `trades_round_3_day_{0,1,2}.csv` and produces, per
counterparty (`buyer` and `seller`), a profit-at-horizon score:

    horizon_pnl(trade) = (mid_price[ts + horizon] - trade_price) * quantity  (buy)
    horizon_pnl(trade) = (trade_price - mid_price[ts + horizon]) * quantity  (sell)

Output
------
Per-(day, product, counterparty) rollup with total signed flow, mean
horizon PnL, and count. Counterparties whose horizon PnL is materially
non-zero are planted actors — copy their buys and fade their sells (or vice
versa), gated on sample size.

Usage
-----
    python3 counterparty_scan.py \
        --dataset-root ../../datasets/round3 \
        --out ../../../prosperity-research/04_signal_notes/round3/counterparty_scan.csv \
        [--horizon 500]
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _as_int(s: str) -> Optional[int]:
    try:
        return int(s)
    except ValueError:
        return None


def _as_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except ValueError:
        return None


def load_mids(prices_path: Path) -> Dict[Tuple[int, str], float]:
    out: Dict[Tuple[int, str], float] = {}
    with prices_path.open() as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            ts = _as_int(row.get("timestamp", ""))
            prod = row.get("product", "")
            mid = _as_float(row.get("mid_price", ""))
            if ts is None or prod == "" or mid is None:
                continue
            out[(ts, prod)] = mid
    return out


def mid_at(
    mids: Dict[Tuple[int, str], float],
    ts: int,
    product: str,
    horizon: int,
) -> Optional[float]:
    # try [ts + horizon, ts + horizon + 100, ...] for up to a few gaps
    for step in range(0, horizon * 4, 100):
        key = (ts + horizon + step, product)
        if key in mids:
            return mids[key]
    return None


def scan_day(
    prices_path: Path,
    trades_path: Path,
    day: int,
    horizon: int,
) -> List[Dict[str, object]]:
    mids = load_mids(prices_path)
    rollup: Dict[Tuple[str, str, str], Dict[str, float]] = defaultdict(
        lambda: {"n_trades": 0.0, "signed_qty": 0.0, "horizon_pnl": 0.0}
    )
    with trades_path.open() as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            ts = _as_int(row.get("timestamp", ""))
            buyer = row.get("buyer", "") or "_anon_"
            seller = row.get("seller", "") or "_anon_"
            symbol = row.get("symbol", "")
            price = _as_float(row.get("price", ""))
            qty = _as_float(row.get("quantity", ""))
            if ts is None or symbol == "" or price is None or qty is None:
                continue
            fut = mid_at(mids, ts, symbol, horizon)
            if fut is None:
                continue
            # buyer's horizon pnl from buying
            pnl_buyer = (fut - price) * qty
            # seller's horizon pnl from selling (they locked price, missed future)
            pnl_seller = (price - fut) * qty

            key_b = (symbol, "buyer", buyer)
            rb = rollup[key_b]
            rb["n_trades"] += 1
            rb["signed_qty"] += qty
            rb["horizon_pnl"] += pnl_buyer

            key_s = (symbol, "seller", seller)
            rs = rollup[key_s]
            rs["n_trades"] += 1
            rs["signed_qty"] += qty
            rs["horizon_pnl"] += pnl_seller

    out: List[Dict[str, object]] = []
    for (symbol, side, cp), stats in rollup.items():
        if stats["n_trades"] == 0:
            continue
        out.append(
            {
                "day": day,
                "product": symbol,
                "side": side,
                "counterparty": cp,
                "n_trades": int(stats["n_trades"]),
                "total_qty": stats["signed_qty"],
                "total_horizon_pnl": round(stats["horizon_pnl"], 4),
                "mean_horizon_pnl": round(
                    stats["horizon_pnl"] / max(stats["signed_qty"], 1.0), 4
                ),
            }
        )
    return out


def main() -> int:
    here = Path(__file__).resolve().parent
    default_data = here.parents[1] / "datasets" / "round3"
    default_out = (
        here.parents[2]
        / "prosperity-research"
        / "04_signal_notes"
        / "round3"
        / "counterparty_scan.csv"
    )
    p = argparse.ArgumentParser()
    p.add_argument("--dataset-root", type=Path, default=default_data)
    p.add_argument("--out", type=Path, default=default_out)
    p.add_argument("--horizon", type=int, default=500)
    args = p.parse_args()

    all_rows: List[Dict[str, object]] = []
    for day in (0, 1, 2):
        prices = args.dataset_root / f"prices_round_3_day_{day}.csv"
        trades = args.dataset_root / f"trades_round_3_day_{day}.csv"
        if not trades.exists() or not prices.exists():
            continue
        all_rows.extend(scan_day(prices, trades, day, args.horizon))

    if not all_rows:
        print("no trades data found; check dataset root")
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "day",
        "product",
        "side",
        "counterparty",
        "n_trades",
        "total_qty",
        "total_horizon_pnl",
        "mean_horizon_pnl",
    ]
    with args.out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(all_rows)
    print(f"wrote {len(all_rows)} counterparty rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
