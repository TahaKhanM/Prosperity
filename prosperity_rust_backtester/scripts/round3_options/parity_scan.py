"""Identity-only arbitrage scanner for the Round 3 voucher chain.

Runs four checks on the per-tick panel produced by `build_voucher_panel.py`:

1. **Intrinsic floor**: V_K >= max(S - K, 0). Violation => long-voucher arb.
2. **Upper bound**:    V_K <= S.                  Violation => short-voucher arb.
3. **Strike monotonicity**: K1 < K2 => V_{K1} >= V_{K2}. Violation => vertical-spread arb.
4. **Convexity (butterfly)**: V_{K1} - 2 V_{K2} + V_{K3} >= 0 for equally
   spaced K1 < K2 < K3. Violation => butterfly arb.

These are *identities*, not statistical bets. Any violation is a bounded-payoff
edge subject only to execution risk. Each violation is emitted with (day, ts,
strikes, mids, edge_size) so downstream tooling can prioritize.

Usage
-----
    python3 parity_scan.py \
        --panel ../../../prosperity-research/03_eda/round3/voucher_panel.csv \
        --out ../../../prosperity-research/04_signal_notes/round3/parity_violations.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional


STRIKES = [4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000, 6500]


def _get_float(row: Dict[str, str], key: str) -> Optional[float]:
    v = row.get(key, "")
    if v == "" or v is None:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def scan_intrinsic_and_upper(
    row: Dict[str, str], s: float
) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for k in STRIKES:
        v = _get_float(row, f"V_{k}")
        if v is None:
            continue
        intrinsic = max(s - k, 0.0)
        if v < intrinsic - 1e-6:
            out.append(
                {
                    "check": "intrinsic_floor",
                    "strike_a": k,
                    "strike_b": "",
                    "strike_c": "",
                    "lhs": v,
                    "rhs": intrinsic,
                    "edge": intrinsic - v,
                }
            )
        if v > s + 1e-6:
            out.append(
                {
                    "check": "upper_bound_S",
                    "strike_a": k,
                    "strike_b": "",
                    "strike_c": "",
                    "lhs": v,
                    "rhs": s,
                    "edge": v - s,
                }
            )
    return out


def scan_monotonicity(row: Dict[str, str]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    strikes_sorted = sorted(STRIKES)
    for i in range(len(strikes_sorted) - 1):
        k1, k2 = strikes_sorted[i], strikes_sorted[i + 1]
        v1 = _get_float(row, f"V_{k1}")
        v2 = _get_float(row, f"V_{k2}")
        if v1 is None or v2 is None:
            continue
        if v1 < v2 - 1e-6:
            out.append(
                {
                    "check": "strike_monotonicity",
                    "strike_a": k1,
                    "strike_b": k2,
                    "strike_c": "",
                    "lhs": v1,
                    "rhs": v2,
                    "edge": v2 - v1,
                }
            )
    return out


def scan_convexity(row: Dict[str, str]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    strikes_sorted = sorted(STRIKES)
    # only equally spaced triples in the sorted list
    for i in range(len(strikes_sorted) - 2):
        k1, k2, k3 = strikes_sorted[i], strikes_sorted[i + 1], strikes_sorted[i + 2]
        if (k2 - k1) != (k3 - k2):
            continue
        v1 = _get_float(row, f"V_{k1}")
        v2 = _get_float(row, f"V_{k2}")
        v3 = _get_float(row, f"V_{k3}")
        if None in (v1, v2, v3):
            continue
        fly = v1 - 2 * v2 + v3
        if fly < -1e-6:
            out.append(
                {
                    "check": "convexity_butterfly",
                    "strike_a": k1,
                    "strike_b": k2,
                    "strike_c": k3,
                    "lhs": fly,
                    "rhs": 0.0,
                    "edge": -fly,
                }
            )
    return out


def run_scan(panel_path: Path, out_path: Path) -> Dict[str, int]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows_out: List[Dict[str, object]] = []
    counts: Dict[str, int] = {}
    with panel_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            s = _get_float(row, "S")
            if s is None:
                continue
            violations = (
                scan_intrinsic_and_upper(row, s)
                + scan_monotonicity(row)
                + scan_convexity(row)
            )
            for v in violations:
                v_full = {
                    "day": int(row.get("day", -1)),
                    "timestamp": int(row.get("timestamp", -1)),
                    "S": s,
                    **v,
                }
                rows_out.append(v_full)
                counts[str(v["check"])] = counts.get(str(v["check"]), 0) + 1

    if rows_out:
        columns = [
            "day",
            "timestamp",
            "S",
            "check",
            "strike_a",
            "strike_b",
            "strike_c",
            "lhs",
            "rhs",
            "edge",
        ]
        with out_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=columns)
            w.writeheader()
            w.writerows(rows_out)
    return counts


def main() -> int:
    here = Path(__file__).resolve().parent
    default_panel = (
        here.parents[2]
        / "prosperity-research"
        / "03_eda"
        / "round3"
        / "voucher_panel.csv"
    )
    default_out = (
        here.parents[2]
        / "prosperity-research"
        / "04_signal_notes"
        / "round3"
        / "parity_violations.csv"
    )
    p = argparse.ArgumentParser()
    p.add_argument("--panel", type=Path, default=default_panel)
    p.add_argument("--out", type=Path, default=default_out)
    args = p.parse_args()

    counts = run_scan(args.panel, args.out)
    if not counts:
        print("no parity violations found")
    else:
        for k, v in sorted(counts.items()):
            print(f"{k}: {v}")
        print(f"violations written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
