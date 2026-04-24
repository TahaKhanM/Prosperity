"""Round 3 exhaustive alpha hunt.

Runs axes A..O across HYDROGEL_PACK, VELVETFRUIT_EXTRACT, and the 10 VEV_*
voucher chain. Writes compact JSON + CSV summaries into
prosperity-research/03_eda/round3/notebooks/_cache/ for consumption by the
deliverable writer.

Pure numpy + stdlib. Intended to be re-runnable end-to-end in ~minutes.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

REPO = Path(__file__).resolve().parents[4]
DATA = REPO / "Data" / "ROUND_3"
PANEL = REPO / "prosperity-research" / "03_eda" / "round3" / "voucher_panel.csv"
OUT = Path(__file__).resolve().parent / "_cache"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.append(str(REPO / "prosperity_rust_backtester" / "scripts" / "round3_options"))
from bs import bs_call_price, bs_call_vega, implied_vol_call, bs_call_delta  # noqa: E402
from stat_tests import rho1, hurst, ou_half_life, spectral_peak, variance_ratio  # noqa: E402

STRIKES = [4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000, 6500]
DAYS = [0, 1, 2]
TTE_DAYS_BY_DAY = {0: 8, 1: 7, 2: 6}  # days to expiry at start of file
YEAR = 365.0


# ---------------------------------------------------------------------------
# data loading
# ---------------------------------------------------------------------------

def load_prices_day(day: int) -> Dict[str, np.ndarray]:
    """Return dict of product -> structured arrays with per-tick book data.

    Columns: timestamp, bid1, bq1, bid2, bq2, bid3, bq3, ask1, aq1, ask2, aq2,
    ask3, aq3, mid.
    """
    path = DATA / f"prices_round_3_day_{day}.csv"
    products = {}
    with open(path, "r") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader)
        for row in reader:
            if not row:
                continue
            prod = row[2]
            ts = int(row[1])
            def f_or_nan(i: int) -> float:
                v = row[i]
                return float(v) if v != "" else float("nan")
            rec = (
                ts,
                f_or_nan(3), f_or_nan(4),
                f_or_nan(5), f_or_nan(6),
                f_or_nan(7), f_or_nan(8),
                f_or_nan(9), f_or_nan(10),
                f_or_nan(11), f_or_nan(12),
                f_or_nan(13), f_or_nan(14),
                f_or_nan(15),
            )
            products.setdefault(prod, []).append(rec)

    dtype = [
        ("ts", np.int64),
        ("b1", np.float64), ("bq1", np.float64),
        ("b2", np.float64), ("bq2", np.float64),
        ("b3", np.float64), ("bq3", np.float64),
        ("a1", np.float64), ("aq1", np.float64),
        ("a2", np.float64), ("aq2", np.float64),
        ("a3", np.float64), ("aq3", np.float64),
        ("mid", np.float64),
    ]
    out = {}
    for prod, rows in products.items():
        arr = np.array(rows, dtype=dtype)
        arr.sort(order="ts")
        out[prod] = arr
    return out


def load_trades_day(day: int) -> List[dict]:
    path = DATA / f"trades_round_3_day_{day}.csv"
    out = []
    with open(path, "r") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader)
        for row in reader:
            if not row:
                continue
            out.append({
                "ts": int(row[0]),
                "buyer": row[1] or "",
                "seller": row[2] or "",
                "symbol": row[3],
                "price": float(row[5]),
                "qty": float(row[6]),
            })
    return out


def load_panel() -> Dict[Tuple[int, int], dict]:
    """Return dict keyed by (day, timestamp) -> dict with panel cols."""
    out = {}
    with open(PANEL, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = int(row["day"])
            ts = int(row["timestamp"])
            out[(d, ts)] = row
    return out


# ---------------------------------------------------------------------------
# helper stats
# ---------------------------------------------------------------------------

def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    mask = np.isfinite(a) & np.isfinite(b)
    a = a[mask]
    b = b[mask]
    if len(a) < 3:
        return float("nan")
    a = a - a.mean()
    b = b - b.mean()
    den = math.sqrt((a * a).sum() * (b * b).sum())
    if den <= 0:
        return float("nan")
    return float((a * b).sum() / den)


def _ols_slope_se(y: np.ndarray, x: np.ndarray) -> Tuple[float, float, float]:
    """Return (slope, intercept, se_slope)."""
    y = np.asarray(y, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    mask = np.isfinite(y) & np.isfinite(x)
    y = y[mask]; x = x[mask]
    n = len(y)
    if n < 3:
        return float("nan"), float("nan"), float("nan")
    mx = x.mean(); my = y.mean()
    dx = x - mx; dy = y - my
    sxx = (dx * dx).sum()
    if sxx <= 0:
        return float("nan"), float("nan"), float("nan")
    slope = (dx * dy).sum() / sxx
    intercept = my - slope * mx
    resid = y - (intercept + slope * x)
    dof = max(n - 2, 1)
    sigma2 = (resid * resid).sum() / dof
    se = math.sqrt(sigma2 / sxx) if sigma2 >= 0 else float("nan")
    return float(slope), float(intercept), float(se)


# ===========================================================================
# AXIS A — HYDROGEL_PACK anchor / pinning test
# ===========================================================================

def axis_A_hydrogel_pin(days: Dict[int, Dict[str, np.ndarray]]) -> dict:
    out: dict = {"per_day": {}, "all_days": {}}
    mids_all: List[float] = []
    for d in DAYS:
        arr = days[d]["HYDROGEL_PACK"]
        mid = arr["mid"]
        mid = mid[np.isfinite(mid)]
        per = {
            "n": int(mid.size),
            "mean": float(mid.mean()),
            "median": float(np.median(mid)),
            "std": float(mid.std()),
            "min": float(mid.min()),
            "max": float(mid.max()),
            "frac_within_1": float(np.mean(np.abs(mid - 10000) <= 1)),
            "frac_within_2": float(np.mean(np.abs(mid - 10000) <= 2)),
            "frac_within_5": float(np.mean(np.abs(mid - 10000) <= 5)),
            "rho1": rho1(mid.tolist()),
            "ou_half_life": ou_half_life(mid.tolist()),
            "hurst": hurst(mid.tolist()),
            "vr_k5": variance_ratio(mid.tolist(), 5),
        }
        out["per_day"][d] = per
        mids_all.extend(mid.tolist())
    mids_all_arr = np.array(mids_all)
    out["all_days"] = {
        "n": int(mids_all_arr.size),
        "mean": float(mids_all_arr.mean()),
        "median": float(np.median(mids_all_arr)),
        "std": float(mids_all_arr.std()),
        "min": float(mids_all_arr.min()),
        "max": float(mids_all_arr.max()),
        "frac_within_1": float(np.mean(np.abs(mids_all_arr - 10000) <= 1)),
        "frac_within_2": float(np.mean(np.abs(mids_all_arr - 10000) <= 2)),
        "frac_within_5": float(np.mean(np.abs(mids_all_arr - 10000) <= 5)),
    }
    # residual vs constant 10000, check whiteness via rho1
    resid = mids_all_arr - 10000.0
    out["all_days"]["resid_rho1"] = rho1(resid.tolist())
    out["all_days"]["resid_hurst"] = hurst(resid.tolist())
    out["all_days"]["resid_ou_half_life"] = ou_half_life(resid.tolist())
    return out


# ===========================================================================
# AXIS B — Wall-mid vs top-mid for VELVETFRUIT_EXTRACT
# ===========================================================================

def _wall_mid(arr: np.ndarray, threshold: float = 20.0) -> np.ndarray:
    """Wall mid: mean of the bid/ask level with max volume (excl thin quotes)."""
    n = arr.size
    out = np.full(n, np.nan)
    bids = np.vstack([arr["b1"], arr["b2"], arr["b3"]]).T
    bqs = np.vstack([arr["bq1"], arr["bq2"], arr["bq3"]]).T
    asks = np.vstack([arr["a1"], arr["a2"], arr["a3"]]).T
    aqs = np.vstack([arr["aq1"], arr["aq2"], arr["aq3"]]).T
    for i in range(n):
        bq = bqs[i].copy(); bp = bids[i].copy()
        aq = aqs[i].copy(); ap = asks[i].copy()
        # mask thin levels
        bq = np.where(bq >= threshold, bq, -1.0)
        aq = np.where(aq >= threshold, aq, -1.0)
        if np.all(bq < 0) or np.all(aq < 0):
            continue
        bi = int(np.nanargmax(bq))
        ai = int(np.nanargmax(aq))
        bp_ = bp[bi]; ap_ = ap[ai]
        if not (math.isfinite(bp_) and math.isfinite(ap_)):
            continue
        out[i] = 0.5 * (bp_ + ap_)
    return out


def axis_B_ve_wall_mid(days: Dict[int, Dict[str, np.ndarray]]) -> dict:
    out = {"per_day": {}}
    horizons = [1, 5, 10, 50]
    for d in DAYS:
        arr = days[d]["VELVETFRUIT_EXTRACT"]
        mid = arr["mid"]
        wall = _wall_mid(arr, threshold=20.0)
        # Future mid change prediction
        per = {"n": int(mid.size)}
        for h in horizons:
            # predict mid[t+h] - mid[t] using (wall[t] - mid[t])
            x = (wall - mid)[:-h]
            y = (mid[h:] - mid[:-h])
            r = _pearson(x, y)
            slope, intercept, se = _ols_slope_se(y, x)
            per[f"h{h}_corr"] = r
            per[f"h{h}_slope"] = slope
            per[f"h{h}_se"] = se
            per[f"h{h}_tstat"] = slope / se if se and se > 0 else float("nan")
        # Baseline: top mid vs its own lag
        x2 = mid[1:] - mid[:-1]
        per["mid_return_rho1"] = rho1(x2.tolist())
        per["wall_defined_frac"] = float(np.mean(np.isfinite(wall)))
        out["per_day"][d] = per
    return out


# ===========================================================================
# AXIS C — Top-k OB imbalance signals on both delta-1 products
# ===========================================================================

def _imbalance(arr: np.ndarray, k: int) -> np.ndarray:
    b = np.zeros(arr.size); a = np.zeros(arr.size)
    for j in range(1, k + 1):
        bqj = arr[f"bq{j}"]; aqj = arr[f"aq{j}"]
        b += np.nan_to_num(bqj, nan=0.0)
        a += np.nan_to_num(aqj, nan=0.0)
    total = b + a
    imb = np.where(total > 0, (b - a) / total, 0.0)
    return imb


def axis_C_imbalance(days: Dict[int, Dict[str, np.ndarray]]) -> dict:
    out: dict = {"per_day": {}}
    products = ["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT"]
    horizons = [1, 5, 10, 100]
    for d in DAYS:
        per_prod = {}
        for p in products:
            arr = days[d][p]
            mid = arr["mid"]
            rec = {}
            for k in [1, 2, 3]:
                imb = _imbalance(arr, k)
                for h in horizons:
                    x = imb[:-h]
                    y = mid[h:] - mid[:-h]
                    r = _pearson(x, y)
                    slope, _, se = _ols_slope_se(y, x)
                    rec[f"k{k}_h{h}_corr"] = r
                    rec[f"k{k}_h{h}_slope"] = slope
                    rec[f"k{k}_h{h}_tstat"] = slope / se if se and se > 0 else float("nan")
            per_prod[p] = rec
        out["per_day"][d] = per_prod
    return out


# ===========================================================================
# AXIS D — Per-counterparty horizon-PnL scan (all anon in R3)
# ===========================================================================

def axis_D_counterparty(days_trades: Dict[int, List[dict]]) -> dict:
    """Horizon PnL per counterparty (same logic as counterparty_scan.py) +
    aggregate by side/product. In Round 3 historical, buyer/seller strings
    are empty, so this is diagnostic only.
    """
    out: dict = {"named_counterparties": set(), "per_day": {}}
    horizon_ts = 100  # 1 tick horizon for quick estimate
    for d in DAYS:
        trades = days_trades[d]
        named = set()
        for t in trades:
            if t["buyer"]:
                named.add(t["buyer"])
            if t["seller"]:
                named.add(t["seller"])
        out["per_day"][d] = {
            "n_trades": len(trades),
            "named_count": len(named),
            "named": sorted(named),
        }
        out["named_counterparties"].update(named)
    out["named_counterparties"] = sorted(out["named_counterparties"])
    return out


# ===========================================================================
# AXIS E — Deep-ITM "no time value" test for VEV_4000, VEV_4500
# ===========================================================================

def axis_E_deep_itm_time_value(panel: Dict[Tuple[int, int], dict]) -> dict:
    out: dict = {}
    for k in [4000, 4500, 5000]:
        per_day = {}
        all_tv: List[float] = []
        for d in DAYS:
            tvs = []
            for key, row in panel.items():
                if key[0] != d:
                    continue
                tv = float(row[f"time_value_{k}"])
                tvs.append(tv)
            arr = np.array(tvs)
            per_day[d] = {
                "n": int(arr.size),
                "mean": float(arr.mean()),
                "median": float(np.median(arr)),
                "std": float(arr.std()),
                "min": float(arr.min()),
                "max": float(arr.max()),
                "frac_zero_or_neg": float(np.mean(arr <= 0.0)),
                "frac_le_0_5": float(np.mean(arr <= 0.5)),
                "frac_ge_1": float(np.mean(arr >= 1.0)),
            }
            all_tv.extend(tvs)
        arr_all = np.array(all_tv)
        per_day["all_days"] = {
            "n": int(arr_all.size),
            "mean": float(arr_all.mean()),
            "median": float(np.median(arr_all)),
            "std": float(arr_all.std()),
            "min": float(arr_all.min()),
            "max": float(arr_all.max()),
            "frac_zero_or_neg": float(np.mean(arr_all <= 0.0)),
            "frac_le_0_5": float(np.mean(arr_all <= 0.5)),
        }
        out[k] = per_day
    return out


# ===========================================================================
# AXIS F — Vol-smile stability (intra-day + across days)
# ===========================================================================

def axis_F_smile_stability() -> dict:
    coeffs_path = REPO / "prosperity-research" / "04_signal_notes" / "round3" / "vol_surface_coeffs.csv"
    per_day: Dict[int, dict] = {}
    rows_by_day: Dict[int, List[Tuple[float, float, float]]] = {d: [] for d in DAYS}
    with open(coeffs_path, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            d = int(r["day"])
            rows_by_day[d].append((
                float(r["atm_iv"]),
                float(r["skew"]),
                float(r["convexity"]),
            ))
    all_atm: List[float] = []
    all_skew: List[float] = []
    all_conv: List[float] = []
    for d in DAYS:
        rows = np.array(rows_by_day[d])
        per_day[d] = {
            "n": int(rows.shape[0]),
            "atm_iv_mean": float(rows[:, 0].mean()),
            "atm_iv_std": float(rows[:, 0].std()),
            "skew_mean": float(rows[:, 1].mean()),
            "skew_std": float(rows[:, 1].std()),
            "convexity_mean": float(rows[:, 2].mean()),
            "convexity_std": float(rows[:, 2].std()),
            "atm_iv_rho1": rho1(rows[:, 0].tolist()),
            "atm_iv_half_life": ou_half_life(rows[:, 0].tolist()),
        }
        all_atm.extend(rows[:, 0].tolist())
        all_skew.extend(rows[:, 1].tolist())
        all_conv.extend(rows[:, 2].tolist())
    all_atm_arr = np.array(all_atm)
    all_skew_arr = np.array(all_skew)
    all_conv_arr = np.array(all_conv)
    return {
        "per_day": per_day,
        "all_days": {
            "atm_iv_mean": float(all_atm_arr.mean()),
            "atm_iv_std": float(all_atm_arr.std()),
            "skew_mean": float(all_skew_arr.mean()),
            "skew_std": float(all_skew_arr.std()),
            "convexity_mean": float(all_conv_arr.mean()),
            "convexity_std": float(all_conv_arr.std()),
            "frozen_smile_recommendation": {
                "atm_iv": float(np.median(all_atm_arr)),
                "skew": float(np.median(all_skew_arr)),
                "convexity": float(np.median(all_conv_arr)),
            },
        },
    }


# ===========================================================================
# AXIS G — Vol-surface residual mean-reversion per strike
# ===========================================================================

def axis_G_residual_mean_reversion() -> dict:
    resid_path = REPO / "prosperity-research" / "04_signal_notes" / "round3" / "vol_surface_residuals.csv"
    by_strike: Dict[int, List[float]] = {k: [] for k in STRIKES}
    with open(resid_path, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            k = int(r["strike"])
            v = r["iv_resid"]
            if v == "" or v == "nan":
                continue
            by_strike[k].append(float(v))
    out = {}
    for k in STRIKES:
        series = by_strike[k]
        if len(series) < 50:
            out[k] = {"n": len(series), "skipped": True}
            continue
        out[k] = {
            "n": len(series),
            "mean": float(np.mean(series)),
            "std": float(np.std(series)),
            "rho1": rho1(series),
            "ou_half_life": ou_half_life(series),
            "hurst": hurst(series),
            "vr_k5": variance_ratio(series, 5),
        }
    return out


# ===========================================================================
# AXIS H — Parity arbs on tradeable sides (best_bid / best_ask)
# ===========================================================================

def axis_H_parity_tradeable(days: Dict[int, Dict[str, np.ndarray]]) -> dict:
    """Count arbs measured on the tradeable side with edge >= 1 per day,
    separately by check type.

    Floor: best_ask(K) + 1 < max(S_ask - K, 0)  — use S ask side
    Cap:   best_bid(K) > S_bid + 1
    Mono:  best_bid(K1) > best_ask(K2) + 1 for K1 < K2
    """
    out = {"per_day": {}}
    for d in DAYS:
        ve = days[d]["VELVETFRUIT_EXTRACT"]
        n = ve.size
        S_ask = ve["a1"]
        S_bid = ve["b1"]
        voucher_arrs = {k: days[d][f"VEV_{k}"] for k in STRIKES}
        counts = {"floor": 0, "cap": 0, "mono": 0}
        edges = {"floor": [], "cap": [], "mono": []}
        for k, arr in voucher_arrs.items():
            best_ask_v = arr["a1"]
            best_bid_v = arr["b1"]
            intrinsic_ask = np.maximum(S_ask - k, 0.0)
            mask = np.isfinite(best_ask_v) & np.isfinite(S_ask) & (intrinsic_ask - best_ask_v >= 1)
            counts["floor"] += int(mask.sum())
            edges["floor"].extend((intrinsic_ask - best_ask_v)[mask].tolist())
            mask2 = np.isfinite(best_bid_v) & np.isfinite(S_bid) & (best_bid_v - S_bid >= 1)
            counts["cap"] += int(mask2.sum())
            edges["cap"].extend((best_bid_v - S_bid)[mask2].tolist())
        strikes_sorted = sorted(voucher_arrs.keys())
        for i, k1 in enumerate(strikes_sorted):
            for k2 in strikes_sorted[i + 1:]:
                a1 = voucher_arrs[k1]["a1"]
                b1 = voucher_arrs[k1]["b1"]
                a2 = voucher_arrs[k2]["a1"]
                b2 = voucher_arrs[k2]["b1"]
                mask = np.isfinite(b1) & np.isfinite(a2) & (b1 - a2 >= 1)
                counts["mono"] += int(mask.sum())
                edges["mono"].extend((b1 - a2)[mask].tolist())
        out["per_day"][d] = {
            "counts": counts,
            "edge_stats": {
                c: {
                    "n": len(edges[c]),
                    "mean": float(np.mean(edges[c])) if edges[c] else 0.0,
                    "max": float(np.max(edges[c])) if edges[c] else 0.0,
                    "sum": float(np.sum(edges[c])) if edges[c] else 0.0,
                }
                for c in counts
            },
        }
    return out


# ===========================================================================
# AXIS I — Intra-day seasonality
# ===========================================================================

def axis_I_seasonality(days: Dict[int, Dict[str, np.ndarray]]) -> dict:
    """Binned average return per tick-of-day across days for each product."""
    # bucket by tick index: ts // 100 is 0..9999
    out = {"products": {}}
    prods = ["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT"] + [f"VEV_{k}" for k in STRIKES[:8]]  # skip 6000,6500 (stuck)
    bucket_size = 500  # 500 ticks per bucket = 20 buckets
    for p in prods:
        # pool ticks-of-day across 3 days
        returns_by_bucket: Dict[int, List[float]] = defaultdict(list)
        mids_by_bucket: Dict[int, List[float]] = defaultdict(list)
        for d in DAYS:
            arr = days[d][p]
            ts = arr["ts"]
            mid = arr["mid"]
            # 1-tick (=100 ts) returns
            dm = np.diff(mid)
            for i in range(len(dm)):
                t = ts[i]
                bucket = t // (bucket_size * 100)
                if math.isfinite(dm[i]):
                    returns_by_bucket[int(bucket)].append(float(dm[i]))
                if math.isfinite(mid[i]):
                    mids_by_bucket[int(bucket)].append(float(mid[i]))
        # compute z-scores per bucket vs overall mean
        all_r = []
        for lst in returns_by_bucket.values():
            all_r.extend(lst)
        mu = float(np.mean(all_r)) if all_r else 0.0
        sd = float(np.std(all_r)) if all_r else 1.0
        buckets_out = {}
        for b, lst in sorted(returns_by_bucket.items()):
            m = float(np.mean(lst))
            se = sd / math.sqrt(len(lst)) if lst else float("nan")
            z = (m - mu) / se if se and se > 0 else float("nan")
            buckets_out[b] = {
                "n": len(lst),
                "mean_return": m,
                "se": se,
                "z": z,
                "mid_mean": float(np.mean(mids_by_bucket[b])) if mids_by_bucket[b] else float("nan"),
            }
        # flag extreme buckets
        flagged = [(b, v["z"], v["mean_return"]) for b, v in buckets_out.items() if math.isfinite(v["z"]) and abs(v["z"]) > 3]
        out["products"][p] = {
            "bucket_size_ticks": bucket_size,
            "mean_return_per_tick": mu,
            "std_return": sd,
            "flagged_buckets": flagged,
            "n_flagged": len(flagged),
        }
    return out


# ===========================================================================
# AXIS J — Cross-asset lead-lag
# ===========================================================================

def axis_J_leadlag(days: Dict[int, Dict[str, np.ndarray]]) -> dict:
    """Cross-correlation of returns over lags -10..+10 for pairs."""
    prods = ["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT"] + [f"VEV_{k}" for k in [4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500]]
    # Build concatenated returns across 3 days (careful: break at boundaries)
    series_by_prod: Dict[str, List[float]] = {p: [] for p in prods}
    for d in DAYS:
        for p in prods:
            arr = days[d][p]
            mid = arr["mid"]
            dm = np.diff(mid)
            # Use finite diffs only; replace nan with 0 for cross-correlation
            dm = np.nan_to_num(dm, nan=0.0)
            series_by_prod[p].extend(dm.tolist())
    # Pairwise cross-correlation
    lags = list(range(-10, 11))
    results = []
    prod_arr = {p: np.array(series_by_prod[p]) for p in prods}
    for i, p1 in enumerate(prods):
        for p2 in prods[i + 1:]:
            a = prod_arr[p1]; b = prod_arr[p2]
            n = min(len(a), len(b))
            a = a[:n]; b = b[:n]
            a = a - a.mean(); b = b - b.mean()
            den = math.sqrt((a * a).sum() * (b * b).sum())
            if den <= 0:
                continue
            best_lag, best_c = 0, 0.0
            for lag in lags:
                if lag >= 0:
                    x = a[:n - lag] if lag > 0 else a
                    y = b[lag:] if lag > 0 else b
                else:
                    x = a[-lag:]
                    y = b[:n + lag]
                if len(x) < 50:
                    continue
                c = float((x * y).sum() / den)
                if abs(c) > abs(best_c):
                    best_c = c
                    best_lag = lag
            results.append({
                "p1": p1, "p2": p2, "best_lag": best_lag, "corr_at_best_lag": best_c,
                "corr_lag0": float((a[:n] * b[:n]).sum() / den),
            })
    # top-10 by abs corr
    results.sort(key=lambda r: -abs(r["corr_at_best_lag"]))
    return {"pairs_ranked": results[:10], "pairs_all_n": len(results)}


# ===========================================================================
# AXIS K — Volatility clustering / GARCH-lite
# ===========================================================================

def axis_K_vol_clustering(days: Dict[int, Dict[str, np.ndarray]]) -> dict:
    out = {"products": {}}
    prods = ["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT"] + [f"VEV_{k}" for k in [5100, 5200, 5300]]
    for p in prods:
        absrets = []
        for d in DAYS:
            arr = days[d][p]
            mid = arr["mid"]
            dm = np.diff(mid)
            dm = dm[np.isfinite(dm)]
            absrets.extend(np.abs(dm).tolist())
        r1 = rho1(absrets)
        out["products"][p] = {
            "n": len(absrets),
            "abs_return_mean": float(np.mean(absrets)),
            "abs_return_std": float(np.std(absrets)),
            "abs_return_rho1": r1,
            "clustering": r1 > 0.05,
        }
    return out


# ===========================================================================
# AXIS L — Trade size distribution
# ===========================================================================

def axis_L_trade_sizes(days_trades: Dict[int, List[dict]]) -> dict:
    """Histogram trade sizes per product across all 3 days + bot-modal detection."""
    sizes: Dict[str, List[float]] = defaultdict(list)
    for d in DAYS:
        for t in days_trades[d]:
            sizes[t["symbol"]].append(float(t["qty"]))
    out = {}
    for p, lst in sizes.items():
        arr = np.array(lst)
        # unique counts
        unique, counts = np.unique(arr.astype(int), return_counts=True)
        topmodes = sorted(zip(unique.tolist(), counts.tolist()), key=lambda x: -x[1])[:5]
        out[p] = {
            "n": int(arr.size),
            "mean": float(arr.mean()),
            "median": float(np.median(arr)),
            "max": float(arr.max()),
            "top_modes": topmodes,
        }
    return out


# ===========================================================================
# AXIS M — Frequency domain spectral peak on each product's mid series
# ===========================================================================

def axis_M_spectral(days: Dict[int, Dict[str, np.ndarray]]) -> dict:
    out = {"products": {}}
    prods = ["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT"] + [f"VEV_{k}" for k in [4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500]]
    for p in prods:
        # use day 0 only to keep n tractable (spectral_peak is O(n^2))
        arr = days[0][p]
        mid = arr["mid"]
        mid = mid[np.isfinite(mid)]
        # subsample every 10 for speed
        mid = mid[::10][:1000]
        if len(mid) < 32:
            continue
        per, power = spectral_peak(mid.tolist())
        out["products"][p] = {
            "n_used": len(mid),
            "dominant_period_samples": per,
            "dominant_period_ticks": per * 10,
            "power": power,
        }
    return out


# ===========================================================================
# AXIS N — End-of-day drift
# ===========================================================================

def axis_N_eod(days: Dict[int, Dict[str, np.ndarray]]) -> dict:
    """Last-N-tick behavior for VE and vouchers."""
    out = {"products": {}}
    prods = ["VELVETFRUIT_EXTRACT"] + [f"VEV_{k}" for k in [4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500]]
    for p in prods:
        per_day = {}
        for d in DAYS:
            arr = days[d][p]
            mid = arr["mid"]
            ts = arr["ts"]
            # last 50 ticks
            last50 = mid[-50:]
            last10 = mid[-10:]
            last5 = mid[-5:]
            rest = mid[:-50]
            per_day[d] = {
                "mid_overall_mean": float(np.nanmean(rest)) if rest.size else float("nan"),
                "mid_last50_mean": float(np.nanmean(last50)),
                "mid_last10_mean": float(np.nanmean(last10)),
                "mid_last5_mean": float(np.nanmean(last5)),
                "drift_last50": float(np.nanmean(last50) - np.nanmean(rest)) if rest.size else float("nan"),
                "drift_last5": float(np.nanmean(last5) - np.nanmean(rest)) if rest.size else float("nan"),
            }
        out["products"][p] = per_day
    return out


# ===========================================================================
# AXIS O — Implied forward from voucher chain
# ===========================================================================

def axis_O_implied_forward(days: Dict[int, Dict[str, np.ndarray]], panel: Dict[Tuple[int, int], dict]) -> dict:
    """For a fixed frozen-smile guess, back out the forward F that minimizes
    IV dispersion across strikes. Simple bisection in F at a snapshot.
    """
    # Take 3 snapshots: day0 ts=100000, day1 ts=500000, day2 ts=900000
    snapshots = [(0, 100000), (1, 500000), (2, 900000)]
    tte_years_by_day = {0: 8 / YEAR, 1: 7 / YEAR, 2: 6 / YEAR}

    def iv_dispersion(F: float, row: dict, tte: float) -> float:
        ivs = []
        for k in [5000, 5100, 5200, 5300, 5400, 5500]:
            V = float(row[f"V_{k}"])
            iv = implied_vol_call(V, F, k, tte, 0.0)
            if iv and math.isfinite(iv):
                ivs.append(iv)
        if len(ivs) < 3:
            return float("nan")
        return float(np.std(ivs))

    out = {"snapshots": []}
    for (d, ts) in snapshots:
        row = panel.get((d, ts))
        if not row:
            continue
        S = float(row["S"])
        tte = tte_years_by_day[d]
        # search F in [S*0.95, S*1.05] by grid
        grid = np.linspace(S * 0.95, S * 1.05, 41)
        disps = [iv_dispersion(float(F), row, tte) for F in grid]
        valid = [(F, x) for F, x in zip(grid, disps) if math.isfinite(x)]
        if not valid:
            continue
        F_star, d_star = min(valid, key=lambda t: t[1])
        d_at_S = iv_dispersion(S, row, tte)
        out["snapshots"].append({
            "day": d, "ts": ts, "S": S, "F_star": float(F_star),
            "basis": float(F_star - S), "basis_bps": float((F_star - S) / S * 1e4),
            "disp_at_F_star": d_star, "disp_at_S": d_at_S,
        })
    return out


# ===========================================================================
# Main
# ===========================================================================

def main():
    print("Loading data ...")
    days_data = {d: load_prices_day(d) for d in DAYS}
    days_trades = {d: load_trades_day(d) for d in DAYS}
    panel = load_panel()
    print(f"panel rows: {len(panel)}")

    axes = {}

    print("Axis A: hydrogel pin test ...")
    axes["A"] = axis_A_hydrogel_pin(days_data)

    print("Axis B: VE wall mid ...")
    axes["B"] = axis_B_ve_wall_mid(days_data)

    print("Axis C: OB imbalance ...")
    axes["C"] = axis_C_imbalance(days_data)

    print("Axis D: counterparty ...")
    axes["D"] = axis_D_counterparty(days_trades)

    print("Axis E: deep-ITM time value ...")
    axes["E"] = axis_E_deep_itm_time_value(panel)

    print("Axis F: smile stability ...")
    axes["F"] = axis_F_smile_stability()

    print("Axis G: residual mean reversion ...")
    axes["G"] = axis_G_residual_mean_reversion()

    print("Axis H: parity tradeable ...")
    axes["H"] = axis_H_parity_tradeable(days_data)

    print("Axis I: seasonality ...")
    axes["I"] = axis_I_seasonality(days_data)

    print("Axis J: lead-lag ...")
    axes["J"] = axis_J_leadlag(days_data)

    print("Axis K: vol clustering ...")
    axes["K"] = axis_K_vol_clustering(days_data)

    print("Axis L: trade sizes ...")
    axes["L"] = axis_L_trade_sizes(days_trades)

    print("Axis M: spectral ...")
    axes["M"] = axis_M_spectral(days_data)

    print("Axis N: end-of-day drift ...")
    axes["N"] = axis_N_eod(days_data)

    print("Axis O: implied forward ...")
    axes["O"] = axis_O_implied_forward(days_data, panel)

    # Write to disk as JSON (pretty)
    out_path = OUT / "axes_results.json"
    with open(out_path, "w") as f:
        json.dump(axes, f, indent=2, default=str)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
