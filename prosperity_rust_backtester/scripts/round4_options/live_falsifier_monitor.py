"""live_falsifier_monitor.py — operational monitor for r4_final_v01.

Reads a fresh combined.log from a live R4 submission (or a Rust BT
combined.log) and re-checks the four aggregate falsifier triggers
documented in r4_final_v01.py:

  1. Mean h=100 mid-after-Mark-14-print on HYD < +2.0 (was +8.65 historical).
  2. Mark 14 ↔ Mark 38 pairing rate on HYD < 70 % (was 97.7 % historical).
  3. Mean h=5 mid-after-Mark-67-buy on VFE < +0.5 ticks.
  4. Live PnL < r4_mark_lean_v01 fallback by > 500 XIRECS on day 1 → revert
     to v15 baseline for day 2.

Usage:
    python3 live_falsifier_monitor.py <combined.log> \\
        [--live-pnl X --v01-pnl Y] [--out FILE | --no-out]

Exits 0 if all checks PASS or SKIP; exits 1 if any FAIL. Writes a summary
to prosperity-research/04_signal_notes/round4/live_falsifier_check_<date>.md
unless --no-out is given.

The combined.log is the standard Prosperity Rust BT output (sections:
"Sandbox logs:" / "Activities log:" / "Trade History:"). The script
parses Activities (semicolon-CSV with mid_price) for mids, and
Trade History (JSON array) for buyer/seller-tagged trades.

Stdlib-only. Compatible with Python 3.8+.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------- Falsifier thresholds (from r4_final_v01.py docstring) ---------

ADV_H100_HYD_M14_MIN = 2.0       # historical was +8.65
PAIRING_RATE_HYD_MIN = 0.70      # historical was 0.977
ADV_H5_VFE_M67_MIN = 0.5
DAY1_PNL_DEFICIT_MAX = 500.0     # vs v01 fallback


# ---------- combined.log parsing ------------------------------------------


def split_sections(log_path: Path) -> Dict[str, str]:
    """Return {section_name: section_body} for the three labeled sections."""
    text = log_path.read_text()
    sections: Dict[str, str] = {}
    # Section markers are line-anchored.
    markers = ["Sandbox logs:", "Activities log:", "Trade History:"]
    indices = []
    for m in markers:
        idx = text.find("\n" + m + "\n")
        if idx == -1 and text.startswith(m + "\n"):
            idx = 0
        elif idx != -1:
            idx += 1  # skip leading newline
        indices.append(idx)
    indices.append(len(text))
    for i, m in enumerate(markers):
        start = indices[i]
        if start == -1:
            continue
        # next non -1 index after this one
        end = len(text)
        for j in range(i + 1, len(markers)):
            if indices[j] != -1:
                end = indices[j]
                break
        # body excludes the marker line itself
        body_start = text.find("\n", start) + 1
        sections[m] = text[body_start:end]
    return sections


def parse_activities_mids(activities: str) -> Dict[str, List[Tuple[int, float]]]:
    """Parse the Activities log section into per-product (ts, mid) lists."""
    out: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
    if not activities.strip():
        return out
    f = io.StringIO(activities)
    reader = csv.DictReader(f, delimiter=";")
    for row in reader:
        try:
            ts = int(row["timestamp"])
            product = row["product"]
            mid_str = row.get("mid_price", "").strip()
            if not mid_str:
                continue
            mid = float(mid_str)
            out[product].append((ts, mid))
        except (KeyError, ValueError):
            continue
    return out


def parse_trade_history(history: str) -> List[Dict[str, Any]]:
    """Parse the Trade History section (JSON array)."""
    s = history.strip()
    if not s:
        return []
    # Strip any leading/trailing junk; expect a JSON array.
    start = s.find("[")
    end = s.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        arr = json.loads(s[start:end + 1])
    except json.JSONDecodeError:
        return []
    out: List[Dict[str, Any]] = []
    for entry in arr:
        if not isinstance(entry, dict):
            continue
        try:
            out.append({
                "ts": int(entry["timestamp"]),
                "product": entry["symbol"],
                "price": float(entry["price"]),
                "qty": int(entry["quantity"]),
                "buyer": entry.get("buyer", "") or "",
                "seller": entry.get("seller", "") or "",
            })
        except (KeyError, ValueError, TypeError):
            continue
    return out


def find_mid_at(series: List[Tuple[int, float]], target_ts: int) -> Optional[float]:
    """Latest mid at ts <= target_ts, or None."""
    found: Optional[float] = None
    for ts, mid in series:
        if ts <= target_ts:
            found = mid
        else:
            break
    return found


# ---------- Falsifier checks ----------------------------------------------


def check_mark14_hyd_h100(trades: List[Dict[str, Any]],
                          mids: Dict[str, List[Tuple[int, float]]]
                         ) -> Tuple[str, float, int]:
    hyd_mids = mids.get("HYDROGEL_PACK", [])
    movements: List[float] = []
    for t in trades:
        if t["product"] != "HYDROGEL_PACK":
            continue
        sgn = 0
        if t["buyer"] == "Mark 14":
            sgn = +1
        elif t["seller"] == "Mark 14":
            sgn = -1
        else:
            continue
        # h=100 in Prosperity ticks = 100 * 100 = 10_000 timestamp units.
        m_now = find_mid_at(hyd_mids, t["ts"])
        m_h100 = find_mid_at(hyd_mids, t["ts"] + 10_000)
        if m_now is None or m_h100 is None:
            continue
        movements.append(sgn * (m_h100 - m_now))
    n = len(movements)
    if n == 0:
        return "SKIP (no Mark 14 HYD prints with full h=100 horizon)", 0.0, 0
    mean = sum(movements) / n
    status = "PASS" if mean >= ADV_H100_HYD_M14_MIN else "FAIL"
    return status, mean, n


def check_pairing_rate(trades: List[Dict[str, Any]]) -> Tuple[str, float, int]:
    n_m14 = 0
    n_pair = 0
    for t in trades:
        if t["product"] != "HYDROGEL_PACK":
            continue
        partner: Optional[str] = None
        if t["buyer"] == "Mark 14":
            partner = t["seller"]
        elif t["seller"] == "Mark 14":
            partner = t["buyer"]
        if partner is None:
            continue
        n_m14 += 1
        if partner == "Mark 38":
            n_pair += 1
    if n_m14 == 0:
        return "SKIP (no Mark 14 HYD prints)", 0.0, 0
    rate = n_pair / n_m14
    status = "PASS" if rate >= PAIRING_RATE_HYD_MIN else "FAIL"
    return status, rate, n_m14


def check_mark67_vfe_h5(trades: List[Dict[str, Any]],
                       mids: Dict[str, List[Tuple[int, float]]]
                       ) -> Tuple[str, float, int]:
    vfe_mids = mids.get("VELVETFRUIT_EXTRACT", [])
    movements: List[float] = []
    for t in trades:
        if t["product"] != "VELVETFRUIT_EXTRACT":
            continue
        if t["buyer"] != "Mark 67":
            continue
        # h=5 in Prosperity ticks = 5 * 100 = 500 timestamp units.
        m_now = find_mid_at(vfe_mids, t["ts"])
        m_h5 = find_mid_at(vfe_mids, t["ts"] + 500)
        if m_now is None or m_h5 is None:
            continue
        movements.append(m_h5 - m_now)
    n = len(movements)
    if n == 0:
        return "SKIP (no Mark 67 VFE buys with full h=5 horizon)", 0.0, 0
    mean = sum(movements) / n
    status = "PASS" if mean >= ADV_H5_VFE_M67_MIN else "FAIL"
    return status, mean, n


def check_pnl_vs_v01(live_pnl: Optional[float],
                     v01_pnl: Optional[float]) -> Tuple[str, float, str]:
    if live_pnl is None or v01_pnl is None:
        return "SKIP (live or v01 PnL not provided)", 0.0, ""
    diff = live_pnl - v01_pnl
    status = "PASS" if diff >= -DAY1_PNL_DEFICIT_MAX else "FAIL"
    note = f"live={live_pnl:+,.0f} vs v01={v01_pnl:+,.0f}"
    return status, diff, note


# ---------- Main ----------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("log", type=Path, nargs="?",
                   help="Path to combined.log from a fresh R4 run.")
    p.add_argument("--out", type=Path,
                   default=None, help="Write report to this file.")
    p.add_argument("--no-out", action="store_true",
                   help="Do not write a report file.")
    p.add_argument("--live-pnl", type=float, default=None,
                   help="Optional: day-1 live PnL for falsifier #4.")
    p.add_argument("--v01-pnl", type=float, default=None,
                   help="Optional: r4_mark_lean_v01 fallback day-1 PnL.")
    args = p.parse_args()

    if args.log is None:
        print("usage: live_falsifier_monitor.py <combined.log> "
              "[--live-pnl X --v01-pnl Y]", file=sys.stderr)
        return 2

    if not args.log.is_file():
        print(f"error: {args.log} not found", file=sys.stderr)
        return 2

    sections = split_sections(args.log)
    activities = sections.get("Activities log:", "")
    history = sections.get("Trade History:", "")
    mids = parse_activities_mids(activities)
    trades = parse_trade_history(history)
    print(f"parsed {len(trades)} trades and "
          f"{sum(len(s) for s in mids.values())} mid samples from {args.log}")

    f1 = check_mark14_hyd_h100(trades, mids)
    f2 = check_pairing_rate(trades)
    f3 = check_mark67_vfe_h5(trades, mids)
    f4 = check_pnl_vs_v01(args.live_pnl, args.v01_pnl)

    overall = "PASS"
    for status, _, _ in (f1, f2, f3, f4):
        if status.startswith("FAIL"):
            overall = "FAIL"
            break

    print(f"\n=== Falsifier check (overall: {overall}) ===")
    print(f"1. Mark 14 HYD h=100 mid-move (≥ +{ADV_H100_HYD_M14_MIN}): "
          f"{f1[0]} (mean {f1[1]:+.3f}, n={f1[2]})")
    print(f"2. Mark 14↔Mark 38 HYD pairing rate (≥ {PAIRING_RATE_HYD_MIN:.0%}): "
          f"{f2[0]} (rate {f2[1]:.1%}, n={f2[2]})")
    print(f"3. Mark 67 VFE h=5 mid-move (≥ +{ADV_H5_VFE_M67_MIN}): "
          f"{f3[0]} (mean {f3[1]:+.3f}, n={f3[2]})")
    print(f"4. Day-1 PnL vs v01 fallback (≥ -{DAY1_PNL_DEFICIT_MAX:.0f}): "
          f"{f4[0]} ({f4[2]}, diff {f4[1]:+.0f})")

    if not args.no_out:
        out_path = args.out
        if out_path is None:
            today = dt.date.today().isoformat()
            base = (Path(__file__).parent.parent.parent.parent /
                    "prosperity-research" / "04_signal_notes" / "round4")
            base.mkdir(parents=True, exist_ok=True)
            out_path = base / f"live_falsifier_check_{today}.md"
        body = (
            f"# Live falsifier check — {dt.date.today().isoformat()}\n\n"
            f"Source log: {args.log}\n\n"
            f"Trades parsed: {len(trades)}\n\n"
            f"## Overall: {overall}\n\n"
            f"| # | Falsifier | Status | Value | n |\n"
            f"|---|---|---|---:|---:|\n"
            f"| 1 | Mark 14 HYD h=100 mid-move ≥ +{ADV_H100_HYD_M14_MIN} | "
            f"{f1[0]} | {f1[1]:+.3f} | {f1[2]} |\n"
            f"| 2 | Mark 14↔Mark 38 HYD pair rate ≥ {PAIRING_RATE_HYD_MIN:.0%} | "
            f"{f2[0]} | {f2[1]:.1%} | {f2[2]} |\n"
            f"| 3 | Mark 67 VFE h=5 mid-move ≥ +{ADV_H5_VFE_M67_MIN} | "
            f"{f3[0]} | {f3[1]:+.3f} | {f3[2]} |\n"
            f"| 4 | Day-1 PnL vs v01 fallback ≥ -{DAY1_PNL_DEFICIT_MAX:.0f} | "
            f"{f4[0]} | {f4[1]:+.0f} | {f4[2]} |\n"
        )
        out_path.write_text(body)
        print(f"\nReport written to {out_path}")

    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
