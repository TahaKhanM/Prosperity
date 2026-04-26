"""Counterparty / Mark-name alpha scanner for Round 4.

Round 4 reveals counterparty IDs in the trades CSVs. The `buyer` and `seller`
fields are populated with strings like `"Mark 14"` (Round 3 had them as
empty strings / None). This is the central new alpha for the round; the
Round 4 hint card "Anticipating Activity" instructs the trader to identify
which Marks are market-makers, which are informed, and which are
liquidity-takers.

This script ingests `trades_round_4_day_{1,2,3}.csv` and produces, per
counterparty (`buyer` and `seller`), a horizon-PnL profile and a temporal
profile.

Definitions
-----------
For each trade `(ts, buyer, seller, symbol, price, qty)`:
    pnl_buyer  = (mid[ts + horizon] - price) * qty
    pnl_seller = (price - mid[ts + horizon]) * qty

Aggregate by (day, product, counterparty, side ∈ {buyer, seller}).

Output
------
1. `counterparty_summary.csv` — per-(day, product, counterparty, side)
   rollup with n_trades, total_qty, mean_trade_price, signed_flow,
   horizon_pnl_500, horizon_pnl_2000.
2. `counterparty_findings.md` — narrative ranking with classification guess.
3. `counterparty_temporal.csv` — per-Mark hour-bucket histogram (hour =
   timestamp // 100000, so 10 buckets across a day of 1,000,000 ts).

Usage
-----
    python3 counterparty_scan.py \
        --dataset-root ../../datasets/round4 \
        --out-dir ../../../prosperity-research/04_signal_notes/round4 \
        [--horizon 500] [--long-horizon 2000]
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
    except (ValueError, TypeError):
        return None


def _as_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def load_mids(prices_path: Path) -> Dict[Tuple[int, str], float]:
    """Return {(timestamp, product): mid_price}."""
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
    mids: Dict[Tuple[int, str], float], ts: int, product: str, horizon: int
) -> Optional[float]:
    # try [ts + horizon, ts + horizon + 100, ...] up to 4× horizon for gaps
    for step in range(0, max(horizon, 100) * 4, 100):
        key = (ts + horizon + step, product)
        if key in mids:
            return mids[key]
    return None


def scan_day(
    prices_path: Path,
    trades_path: Path,
    day: int,
    horizon: int,
    long_horizon: int,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    """Returns (rollup_rows, temporal_rows) for one day."""
    mids = load_mids(prices_path)

    # rollup keyed by (symbol, side, counterparty)
    rollup: Dict[Tuple[str, str, str], Dict[str, float]] = defaultdict(
        lambda: {
            "n_trades": 0.0,
            "signed_qty": 0.0,
            "price_sum": 0.0,
            "horizon_pnl": 0.0,
            "horizon_pnl_long": 0.0,
        }
    )

    # temporal keyed by (counterparty, hour_bucket)
    temporal: Dict[Tuple[str, int], int] = defaultdict(int)

    with trades_path.open() as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            ts = _as_int(row.get("timestamp", ""))
            buyer = (row.get("buyer", "") or "_anon_").strip()
            seller = (row.get("seller", "") or "_anon_").strip()
            symbol = row.get("symbol", "")
            price = _as_float(row.get("price", ""))
            qty = _as_float(row.get("quantity", ""))
            if ts is None or symbol == "" or price is None or qty is None:
                continue

            fut = mid_at(mids, ts, symbol, horizon)
            fut_long = mid_at(mids, ts, symbol, long_horizon)

            # buyer pnl from buying (positive if mid rose)
            if fut is not None:
                pnl_buyer = (fut - price) * qty
                pnl_seller = (price - fut) * qty
            else:
                pnl_buyer = pnl_seller = 0.0
            if fut_long is not None:
                pnl_buyer_l = (fut_long - price) * qty
                pnl_seller_l = (price - fut_long) * qty
            else:
                pnl_buyer_l = pnl_seller_l = 0.0

            for side, cp, pnl_h, pnl_l in (
                ("buyer", buyer, pnl_buyer, pnl_buyer_l),
                ("seller", seller, pnl_seller, pnl_seller_l),
            ):
                key = (symbol, side, cp)
                rb = rollup[key]
                rb["n_trades"] += 1
                rb["signed_qty"] += qty
                rb["price_sum"] += price * qty
                if fut is not None:
                    rb["horizon_pnl"] += pnl_h
                if fut_long is not None:
                    rb["horizon_pnl_long"] += pnl_l

            # temporal: 10 buckets across the day. Day of 1,000,000 ts → 100k each.
            bucket = (ts // 100_000) % 10
            temporal[(buyer, bucket)] += 1
            if seller != buyer:
                temporal[(seller, bucket)] += 1

    rollup_rows: List[Dict[str, object]] = []
    for (symbol, side, cp), stats in rollup.items():
        if stats["n_trades"] == 0:
            continue
        denom = max(stats["signed_qty"], 1.0)
        rollup_rows.append({
            "day": day,
            "product": symbol,
            "side": side,
            "counterparty": cp,
            "n_trades": int(stats["n_trades"]),
            "total_qty": stats["signed_qty"],
            "mean_trade_price": round(stats["price_sum"] / denom, 6),
            "signed_flow": stats["signed_qty"] if side == "buyer" else -stats["signed_qty"],
            "horizon_pnl_500": round(stats["horizon_pnl"], 4),
            "horizon_pnl_2000": round(stats["horizon_pnl_long"], 4),
            "mean_horizon_pnl_500": round(stats["horizon_pnl"] / denom, 4),
        })

    temporal_rows: List[Dict[str, object]] = [
        {"day": day, "counterparty": cp, "hour_bucket": b, "n_trades": n}
        for (cp, b), n in temporal.items()
    ]
    return rollup_rows, temporal_rows


def write_csv(rows: List[Dict[str, object]], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(rows[0].keys())
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, delimiter=";")
        w.writeheader()
        w.writerows(rows)


def write_findings_md(
    rollup_rows: List[Dict[str, object]], out_path: Path
) -> None:
    """Quick-look ranking by mark."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    by_mark: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {"buy_qty": 0.0, "sell_qty": 0.0, "h500": 0.0, "h2000": 0.0}
    )
    for r in rollup_rows:
        cp = str(r["counterparty"])
        if cp == "_anon_":
            continue
        if r["side"] == "buyer":
            by_mark[cp]["buy_qty"] += float(r["total_qty"])  # type: ignore[arg-type]
        else:
            by_mark[cp]["sell_qty"] += float(r["total_qty"])  # type: ignore[arg-type]
        by_mark[cp]["h500"] += float(r["horizon_pnl_500"])  # type: ignore[arg-type]
        by_mark[cp]["h2000"] += float(r["horizon_pnl_2000"])  # type: ignore[arg-type]

    ranked = sorted(by_mark.items(), key=lambda kv: -kv[1]["h500"])

    lines = ["# Counterparty findings (Round 4)\n",
             "| Mark | Buy qty | Sell qty | h500 PnL | per-unit | h2000 PnL | Note |",
             "|---|---|---|---|---|---|---|"]
    for cp, s in ranked:
        gross = s["buy_qty"] + s["sell_qty"]
        per_unit = s["h500"] / max(gross, 1.0)
        if per_unit > 4.0:
            note = "**SMART** — copy"
        elif per_unit < -4.0:
            note = "**BAG-HOLDER** — fade"
        elif per_unit > 0.5:
            note = "lean with"
        elif per_unit < -0.5:
            note = "fade lightly"
        else:
            note = "noise / MM"
        lines.append(
            f"| {cp} | {s['buy_qty']:.0f} | {s['sell_qty']:.0f} | "
            f"{s['h500']:+.0f} | {per_unit:+.2f} | {s['h2000']:+.0f} | {note} |"
        )
    out_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    here = Path(__file__).resolve().parent
    default_data = here.parents[1] / "datasets" / "round4"
    default_out = (
        here.parents[2] / "prosperity-research" / "04_signal_notes" / "round4"
    )
    p = argparse.ArgumentParser()
    p.add_argument("--dataset-root", type=Path, default=default_data)
    p.add_argument("--out-dir", type=Path, default=default_out)
    p.add_argument("--horizon", type=int, default=500)
    p.add_argument("--long-horizon", type=int, default=2000)
    args = p.parse_args()

    all_rollup: List[Dict[str, object]] = []
    all_temporal: List[Dict[str, object]] = []
    for day in (1, 2, 3):
        prices = args.dataset_root / f"prices_round_4_day_{day}.csv"
        trades = args.dataset_root / f"trades_round_4_day_{day}.csv"
        if not (trades.exists() and prices.exists()):
            print(f"skipping day {day}: missing CSV under {args.dataset_root}")
            continue
        r_rows, t_rows = scan_day(prices, trades, day, args.horizon, args.long_horizon)
        all_rollup.extend(r_rows)
        all_temporal.extend(t_rows)

    if not all_rollup:
        print("no trades data found; check dataset root")
        return 1

    write_csv(all_rollup, args.out_dir / "counterparty_scan.csv")
    write_csv(all_temporal, args.out_dir / "counterparty_temporal.csv")
    write_findings_md(all_rollup, args.out_dir / "counterparty_findings.md")
    print(
        f"wrote {len(all_rollup)} rollup rows, {len(all_temporal)} temporal rows "
        f"to {args.out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
