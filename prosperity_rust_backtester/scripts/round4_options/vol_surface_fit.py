"""Per-tick parabolic smile fit in log-moneyness for Round 4.

For each tick of the panel produced by `build_voucher_panel.py`, fit

    IV(m) = a0 + a1 * m + a2 * m^2

where m = log(S / K). Reports per-tick coefficients, ATM IV (m=0), per-strike
residuals, and the time-series of base IV across the historical three days.

No numpy dependency — direct 3x3 normal-equation solve.

Round 3 → Round 4 changes
-------------------------
- Default panel/output paths point at `round4`.
- Logic is unchanged; the smile structure is the same.
- The fitted coefficients should drift across the four R4 TTE buckets
  (7 / 6 / 5 / 4 days). Group output by `tte_years` bucket downstream when
  building TTE-indexed smiles for trader code.

Usage
-----
    python3 vol_surface_fit.py \
        --panel ../../../prosperity-research/03_eda/round4/voucher_panel.csv \
        --out-dir ../../../prosperity-research/04_signal_notes/round4
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple


STRIKES = [4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000, 6500]


def _get_float(row: Dict[str, str], key: str) -> Optional[float]:
    v = row.get(key, "")
    if v == "" or v is None:
        return None
    try:
        f = float(v)
        return f if f == f else None
    except ValueError:
        return None


def _solve_3x3(a: List[List[float]], b: List[float]) -> Optional[List[float]]:
    m = [row + [b[i]] for i, row in enumerate(a)]
    for i in range(3):
        pivot = i
        for r in range(i + 1, 3):
            if abs(m[r][i]) > abs(m[pivot][i]):
                pivot = r
        if abs(m[pivot][i]) < 1e-12:
            return None
        if pivot != i:
            m[i], m[pivot] = m[pivot], m[i]
        inv = 1.0 / m[i][i]
        for j in range(i, 4):
            m[i][j] *= inv
        for r in range(3):
            if r == i:
                continue
            factor = m[r][i]
            for j in range(i, 4):
                m[r][j] -= factor * m[i][j]
    return [m[0][3], m[1][3], m[2][3]]


def fit_parabola(points: List[Tuple[float, float]]) -> Optional[Tuple[float, float, float, float]]:
    n = len(points)
    if n < 3:
        return None
    s0 = float(n)
    s1 = sum(p[0] for p in points)
    s2 = sum(p[0] ** 2 for p in points)
    s3 = sum(p[0] ** 3 for p in points)
    s4 = sum(p[0] ** 4 for p in points)
    t0 = sum(p[1] for p in points)
    t1 = sum(p[0] * p[1] for p in points)
    t2 = sum((p[0] ** 2) * p[1] for p in points)
    sol = _solve_3x3([[s0, s1, s2], [s1, s2, s3], [s2, s3, s4]], [t0, t1, t2])
    if sol is None:
        return None
    a0, a1, a2 = sol
    rss = sum((y - (a0 + a1 * x + a2 * x * x)) ** 2 for x, y in points)
    return a0, a1, a2, rss


def fit_all(panel_path: Path) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    coeffs: List[Dict[str, object]] = []
    residuals: List[Dict[str, object]] = []
    with panel_path.open() as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            day = int(row.get("day", -1))
            ts = int(row.get("timestamp", -1))
            tte = _get_float(row, "tte_years")
            pts: List[Tuple[float, float, int]] = []
            for k in STRIKES:
                m = _get_float(row, f"log_moneyness_{k}")
                iv = _get_float(row, f"iv_{k}")
                if m is None or iv is None:
                    continue
                if iv <= 1e-5:
                    continue  # drop deep-ITM intrinsic floors
                pts.append((m, iv, k))
            if len(pts) < 3:
                continue
            fit = fit_parabola([(x, y) for x, y, _ in pts])
            if fit is None:
                continue
            a0, a1, a2, rss = fit
            coeffs.append({
                "day": day, "timestamp": ts, "tte_years": tte,
                "atm_iv": a0, "skew": a1, "convexity": a2,
                "rss": rss, "n_points": len(pts),
            })
            for x, y, k in pts:
                pred = a0 + a1 * x + a2 * x * x
                residuals.append({
                    "day": day, "timestamp": ts, "strike": k,
                    "log_moneyness": x, "iv": y, "iv_fit": pred, "iv_resid": y - pred,
                })
    return coeffs, residuals


def write_csv(rows: List[Dict[str, object]], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    here = Path(__file__).resolve().parent
    default_panel = (
        here.parents[2] / "prosperity-research" / "03_eda" / "round4" / "voucher_panel.csv"
    )
    default_out = here.parents[2] / "prosperity-research" / "04_signal_notes" / "round4"

    p = argparse.ArgumentParser()
    p.add_argument("--panel", type=Path, default=default_panel)
    p.add_argument("--out-dir", type=Path, default=default_out)
    args = p.parse_args()

    coeffs, residuals = fit_all(args.panel)
    write_csv(coeffs, args.out_dir / "vol_surface_coeffs.csv")
    write_csv(residuals, args.out_dir / "vol_surface_residuals.csv")
    if coeffs:
        atm = sorted(float(r["atm_iv"]) for r in coeffs)
        skew = sorted(float(r["skew"]) for r in coeffs)
        cvx = sorted(float(r["convexity"]) for r in coeffs)
        print(
            f"fitted {len(coeffs)} ticks | "
            f"atm_iv [min={atm[0]:.4f} med={atm[len(atm)//2]:.4f} max={atm[-1]:.4f}] | "
            f"skew_med={skew[len(skew)//2]:.4f} | "
            f"convexity_med={cvx[len(cvx)//2]:.4f}"
        )
    else:
        print("no ticks produced a fit; check the panel for IVs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
