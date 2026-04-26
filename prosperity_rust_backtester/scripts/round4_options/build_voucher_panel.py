"""Build a per-tick voucher panel for Round 4.

Input
-----
Round 4 `prices_round_4_day_{1,2,3}.csv` under a configurable dataset root.
Defaults to the bundled Rust backtester dataset folder.

Output
------
A single panel CSV with one row per (day, timestamp) and columns:
    day, timestamp, tte_days, tte_years,
    S, hydrogel,
    V_K (voucher mid) for every strike,
    intrinsic_K, time_value_K, moneyness_K, log_moneyness_K,
    iv_K  (annualized; `tte_years` chosen by the caller via --year-basis).

No trader imports. No state. Pure stdlib CSV + our `bs.py`.

TTE convention (R4)
-------------------
Round 4 historical day 1 → TTE 7 days
Round 4 historical day 2 → TTE 6 days
Round 4 historical day 3 → TTE 5 days
Round 4 live              → TTE 4 days

(Round 3 used days 0/1/2 → TTE 8/7/6.)

Usage
-----
    python3 build_voucher_panel.py \
        --dataset-root ../../datasets/round4 \
        --out-dir ../../../prosperity-research/03_eda/round4 \
        [--year-basis 365] [--ticks-per-day 100]
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import bs  # local module


STRIKES = [4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000, 6500]
UNDERLYING = "VELVETFRUIT_EXTRACT"
DELTA1_NONHEDGE = "HYDROGEL_PACK"

# TTE at start of each historical day (Round 4 numbering: 1, 2, 3).
TTE_BY_DAY = {1: 7, 2: 6, 3: 5}


def voucher_symbol(k: int) -> str:
    return f"VEV_{k}"


def mid_from_row(row: Dict[str, str]) -> Optional[float]:
    try:
        mid = row.get("mid_price", "")
        if mid == "":
            return None
        return float(mid)
    except ValueError:
        return None


def read_prices_csv(path: Path) -> Dict[Tuple[int, int, str], float]:
    out: Dict[Tuple[int, int, str], float] = {}
    with path.open() as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            try:
                day = int(row["day"])
                ts = int(row["timestamp"])
            except (KeyError, ValueError):
                continue
            product = row.get("product", "")
            mid = mid_from_row(row)
            if mid is None:
                continue
            out[(day, ts, product)] = mid
    return out


def load_day(dataset_root: Path, day: int) -> Dict[Tuple[int, str], float]:
    p = dataset_root / f"prices_round_4_day_{day}.csv"
    raw = read_prices_csv(p)
    return {(ts, prod): mid for (_d, ts, prod), mid in raw.items()}


def build_panel(
    dataset_root: Path,
    year_basis: float,
    ticks_per_day: int,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for day in sorted(TTE_BY_DAY):
        tick_data = load_day(dataset_root, day)
        timestamps = sorted({ts for (ts, _p) in tick_data.keys()})
        day_tte_start = TTE_BY_DAY[day]
        for ts in timestamps:
            s = tick_data.get((ts, UNDERLYING))
            if s is None:
                continue
            # linearly shrink TTE within the day.
            # Prosperity timestamps increment by 100 → 100 ticks per "day".
            progress = (ts // (10_000 // max(ticks_per_day, 1))) / max(
                ticks_per_day, 1
            ) if ticks_per_day else 0.0
            tte_days = day_tte_start - max(0.0, min(1.0, progress))
            tte_years = tte_days / year_basis

            row: Dict[str, object] = {
                "day": day,
                "timestamp": ts,
                "tte_days": round(tte_days, 6),
                "tte_years": round(tte_years, 8),
                "S": s,
                "hydrogel": tick_data.get((ts, DELTA1_NONHEDGE), ""),
            }
            for k in STRIKES:
                sym = voucher_symbol(k)
                v = tick_data.get((ts, sym))
                if v is None:
                    for key in (
                        f"V_{k}",
                        f"intrinsic_{k}",
                        f"time_value_{k}",
                        f"moneyness_{k}",
                        f"log_moneyness_{k}",
                        f"iv_{k}",
                    ):
                        row[key] = ""
                    continue
                intrinsic = max(s - k, 0.0)
                time_value = v - intrinsic
                moneyness = s / k
                log_m = math.log(moneyness)
                iv = bs.implied_vol_call(v, s, float(k), tte_years)
                row[f"V_{k}"] = v
                row[f"intrinsic_{k}"] = intrinsic
                row[f"time_value_{k}"] = round(time_value, 6)
                row[f"moneyness_{k}"] = round(moneyness, 8)
                row[f"log_moneyness_{k}"] = round(log_m, 8)
                row[f"iv_{k}"] = "" if (iv != iv) else round(iv, 8)
            rows.append(row)
    return rows


def write_panel(rows: List[Dict[str, object]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise SystemExit("panel is empty; check dataset root and day files")
    columns = list(rows[0].keys())
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    here = Path(__file__).resolve().parent
    default_data = here.parents[1] / "datasets" / "round4"
    default_out = here.parents[2] / "prosperity-research" / "03_eda" / "round4"

    p = argparse.ArgumentParser()
    p.add_argument("--dataset-root", type=Path, default=default_data)
    p.add_argument("--out-dir", type=Path, default=default_out)
    p.add_argument(
        "--year-basis",
        type=float,
        default=365.0,
        help="Days per year (e.g. 365, 252).",
    )
    p.add_argument("--ticks-per-day", type=int, default=100)
    p.add_argument("--name", default="voucher_panel.csv")
    args = p.parse_args()

    rows = build_panel(args.dataset_root, args.year_basis, args.ticks_per_day)
    out = args.out_dir / args.name
    write_panel(rows, out)
    print(f"wrote {len(rows)} rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
