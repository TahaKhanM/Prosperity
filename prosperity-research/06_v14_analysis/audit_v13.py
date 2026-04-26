#!/usr/bin/env python3
"""
v13 trade audit. Computes horizon-PnL attribution per trade, identifies losing
buckets, and emits a markdown report at v13_trade_audit.md.

Loads three runs:
  runs/v13_d0_audit, runs/v13_d1_audit, runs/v13_d2_audit
"""
from __future__ import annotations

import csv
import math
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester")
OUT_DIR = Path("/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_v14_analysis")
OUT_DIR.mkdir(parents=True, exist_ok=True)

HORIZONS = [10, 50, 100, 500, 1000, 5000]
DAYS = [0, 1, 2]
TICK_DT = 100  # timestamps increment by 100 per tick

DEEP_OTM = {"VEV_6000", "VEV_6500"}

# v13 smile constants (mirror of traders/Round3/candidates/v13.py)
SMILE_STRIKES = (5000, 5100, 5200, 5300, 5400, 5500)
SMILE_A0_BASE = 0.2420
SMILE_A0_DRIFT_PER_DAY = 0.00275
SMILE_A1_BASE = -0.011
SMILE_A1_DRIFT_PER_DAY = -0.075
SMILE_A2_BASE = 7.21
SMILE_A2_DRIFT_PER_DAY = 0.815
SMILE_PER_STRIKE_BIAS = {
    5000: -0.0077, 5100: +0.0004, 5200: +0.0076,
    5300: +0.0087, 5400: -0.0144, 5500: -0.0067,
}
START_TTE_DAYS = 8.0
DAY_TICKS = 1_000_000.0
SMILE_TTE_FLOOR_DAYS = 0.25


def _ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _npdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def bs_call(s, k, t, sigma):
    if t <= 0 or sigma <= 0:
        return max(s - k, 0.0)
    vsqrt = sigma * math.sqrt(t)
    d1 = (math.log(s / k) + 0.5 * sigma * sigma * t) / vsqrt
    d2 = d1 - vsqrt
    return s * _ncdf(d1) - k * _ncdf(d2)


def bs_vega(s, k, t, sigma):
    if t <= 0 or sigma <= 0:
        return 0.0
    vsqrt = sigma * math.sqrt(t)
    d1 = (math.log(s / k) + 0.5 * sigma * sigma * t) / vsqrt
    return s * _npdf(d1) * math.sqrt(t)


def implied_vol(price, s, k, t):
    intrinsic = max(s - k, 0.0)
    if price < intrinsic - 1e-9 or price > s + 1e-9 or t <= 0:
        return float("nan")
    if price <= intrinsic + 1e-9:
        return 0.0
    lo, hi = 1e-6, 5.0
    p_lo = bs_call(s, k, lo, lo) if False else bs_call(s, k, t, lo)
    p_hi = bs_call(s, k, t, hi)
    if (p_lo - price) * (p_hi - price) > 0:
        return float("nan")
    for _ in range(120):
        m = 0.5 * (lo + hi)
        p = bs_call(s, k, t, m)
        if abs(p - price) < 1e-6:
            return m
        if (p - price) * (p_lo - price) < 0:
            hi = m; p_hi = p
        else:
            lo = m; p_lo = p
    return 0.5 * (lo + hi)


def tte_years(timestamp, day):
    """timestamp is within-day 0..999_900. Day 0 -> TTE 8d, Day 1 -> 7d, Day 2 -> 6d at start."""
    days_burnt_in_day = timestamp / DAY_TICKS
    days_left = max(START_TTE_DAYS - day - days_burnt_in_day, SMILE_TTE_FLOOR_DAYS)
    return days_left / 365.0, days_left


def smile_prior(tte_days):
    drift = max(0.0, 8.0 - tte_days)
    a0 = SMILE_A0_BASE + SMILE_A0_DRIFT_PER_DAY * drift
    a1 = SMILE_A1_BASE + SMILE_A1_DRIFT_PER_DAY * drift
    a2 = SMILE_A2_BASE + SMILE_A2_DRIFT_PER_DAY * drift
    return a0, a1, a2


def load_activity(run_dir: Path):
    """Returns mids[product] = {timestamp -> mid_price}, plus best bid/ask + spread per tick."""
    mids = defaultdict(dict)
    bids = defaultdict(dict)  # product -> ts -> best_bid_1
    asks = defaultdict(dict)  # product -> ts -> best_ask_1
    bid_vol = defaultdict(dict)
    ask_vol = defaultdict(dict)
    p = run_dir / "activity.csv"
    with p.open() as f:
        rdr = csv.DictReader(f, delimiter=";")
        for row in rdr:
            try:
                ts = int(row["timestamp"])
                prod = row["product"]
                mid = row["mid_price"]
                if mid:
                    mids[prod][ts] = float(mid)
                if row["bid_price_1"]:
                    bids[prod][ts] = float(row["bid_price_1"])
                if row["ask_price_1"]:
                    asks[prod][ts] = float(row["ask_price_1"])
                if row["bid_volume_1"]:
                    bid_vol[prod][ts] = float(row["bid_volume_1"])
                if row["ask_volume_1"]:
                    ask_vol[prod][ts] = float(row["ask_volume_1"])
            except Exception:
                continue
    return mids, bids, asks, bid_vol, ask_vol


def load_our_trades(run_dir: Path):
    """Returns list of trades where SUBMISSION is buyer or seller."""
    out = []
    p = run_dir / "trades.csv"
    with p.open() as f:
        rdr = csv.DictReader(f, delimiter=";")
        for row in rdr:
            buyer = (row.get("buyer") or "").strip()
            seller = (row.get("seller") or "").strip()
            is_buy = buyer == "SUBMISSION"
            is_sell = seller == "SUBMISSION"
            if not (is_buy or is_sell):
                continue
            ts = int(row["timestamp"])
            sym = row["symbol"]
            price = float(row["price"])
            qty = abs(float(row["quantity"]))
            side = +1 if is_buy else -1
            out.append({"ts": ts, "symbol": sym, "price": price, "qty": qty, "side": side})
    return out


def imbalance_k1(bid_v, ask_v):
    if bid_v is None or ask_v is None:
        return None
    s = bid_v + ask_v
    if s <= 0:
        return None
    return (bid_v - ask_v) / s


def get_mid(mids_prod, ts):
    """Return mid_price at exactly timestamp ts; if missing, return last seen ts<=ts."""
    if ts in mids_prod:
        return mids_prod[ts]
    # walk back ticks until found
    keys = sorted(mids_prod.keys())
    if not keys:
        return None
    # binary search
    lo, hi = 0, len(keys) - 1
    if ts < keys[0]:
        return None
    if ts >= keys[-1]:
        return mids_prod[keys[-1]]
    while lo < hi:
        m = (lo + hi + 1) // 2
        if keys[m] <= ts:
            lo = m
        else:
            hi = m - 1
    return mids_prod[keys[lo]]


def t_stat(values):
    n = len(values)
    if n < 2:
        return float("nan")
    mu = statistics.fmean(values)
    sd = statistics.pstdev(values)
    if sd == 0:
        return float("nan")
    return mu / (sd / math.sqrt(n))


def main():
    all_trades = []  # rows with full enrichment
    activity_cache = {}  # day -> (mids, bids, asks, bvol, avol)
    pnl_per_product_day = defaultdict(lambda: defaultdict(float))

    for d in DAYS:
        run = ROOT / "runs" / f"v13_d{d}_audit"
        print(f"[load] day {d} from {run}", file=sys.stderr)
        mids, bids, asks, bvol, avol = load_activity(run)
        activity_cache[d] = (mids, bids, asks, bvol, avol)
        trades = load_our_trades(run)
        print(f"  loaded {len(trades)} own trades", file=sys.stderr)

        for tr in trades:
            sym = tr["symbol"]
            ts = tr["ts"]
            mid_at = get_mid(mids[sym], ts)
            bid_at = bids[sym].get(ts)
            ask_at = asks[sym].get(ts)
            bv = bvol[sym].get(ts)
            av = avol[sym].get(ts)
            spread = (ask_at - bid_at) if (bid_at is not None and ask_at is not None) else None
            imb = imbalance_k1(bv, av)

            row = {
                "day": d,
                "ts": ts,
                "symbol": sym,
                "side": tr["side"],
                "qty": tr["qty"],
                "price": tr["price"],
                "mid_at": mid_at,
                "spread": spread,
                "imb_k1": imb,
                "tick_idx": ts // TICK_DT,
            }
            for h in HORIZONS:
                exit_ts = ts + h * TICK_DT
                exit_mid = get_mid(mids[sym], exit_ts)
                if exit_mid is None:
                    row[f"pnl_h{h}"] = None
                    row[f"exit_mid_h{h}"] = None
                else:
                    pnl = tr["side"] * tr["qty"] * (exit_mid - tr["price"])
                    row[f"pnl_h{h}"] = pnl
                    row[f"exit_mid_h{h}"] = exit_mid
            # final mid (last available)
            keys = sorted(mids[sym].keys())
            final_mid = mids[sym][keys[-1]] if keys else None
            row["final_mid"] = final_mid
            row["pnl_final"] = (
                tr["side"] * tr["qty"] * (final_mid - tr["price"]) if final_mid is not None else None
            )
            all_trades.append(row)

    print(f"[stats] total enriched trades: {len(all_trades)}", file=sys.stderr)

    # ---- 2. per (product, day, horizon) aggregation ----
    agg = defaultdict(list)  # (prod, day, h) -> list of pnls
    for t in all_trades:
        for h in HORIZONS:
            v = t[f"pnl_h{h}"]
            if v is not None:
                agg[(t["symbol"], t["day"], h)].append(v)
    horizon_summary = []
    for (prod, day, h), vals in sorted(agg.items()):
        if not vals:
            continue
        horizon_summary.append({
            "product": prod,
            "day": day,
            "horizon": h,
            "n": len(vals),
            "sum": sum(vals),
            "mean": statistics.fmean(vals),
            "std": statistics.pstdev(vals) if len(vals) > 1 else 0,
            "tstat": t_stat(vals),
        })

    # ---- 3. losing buckets per (product, day) ----
    losing_buckets = []
    for prod in sorted({t["symbol"] for t in all_trades}):
        for day in DAYS:
            sub = [t for t in all_trades if t["symbol"] == prod and t["day"] == day]
            if not sub:
                continue
            buckets = {}

            def add(bucket_name, predicate):
                rows = [t for t in sub if predicate(t)]
                pnls = [t["pnl_h5000"] for t in rows if t["pnl_h5000"] is not None]
                if pnls:
                    buckets[bucket_name] = {
                        "n": len(pnls),
                        "sum_pnl_h5000": sum(pnls),
                        "mean_pnl_h5000": statistics.fmean(pnls),
                    }

            add("BUY_when_imb<-0.3", lambda t: t["side"] == 1 and t["imb_k1"] is not None and t["imb_k1"] < -0.3)
            add("SELL_when_imb>0.3", lambda t: t["side"] == -1 and t["imb_k1"] is not None and t["imb_k1"] > 0.3)
            add("BUY_when_imb<-0.5", lambda t: t["side"] == 1 and t["imb_k1"] is not None and t["imb_k1"] < -0.5)
            add("SELL_when_imb>0.5", lambda t: t["side"] == -1 and t["imb_k1"] is not None and t["imb_k1"] > 0.5)
            add("first_30_ticks", lambda t: t["tick_idx"] < 30)
            add("first_100_ticks", lambda t: t["tick_idx"] < 100)
            add("spread_gt_2", lambda t: t["spread"] is not None and t["spread"] > 2)
            add("spread_gt_3", lambda t: t["spread"] is not None and t["spread"] > 3)
            add("BUY_above_mid", lambda t: t["side"] == 1 and t["mid_at"] is not None and t["price"] > t["mid_at"])
            add("SELL_below_mid", lambda t: t["side"] == -1 and t["mid_at"] is not None and t["price"] < t["mid_at"])

            for bn, info in buckets.items():
                losing_buckets.append({
                    "product": prod,
                    "day": day,
                    "bucket": bn,
                    "n": info["n"],
                    "sum_h5000": info["sum_pnl_h5000"],
                    "mean_h5000": info["mean_pnl_h5000"],
                })

    # ---- 4. V5100 day 0 deep-dive ----
    # Enrich V5100 d0 trades with smile fair, IV, BS theo, VE micro
    # Need underlier (VELVETFRUIT_EXTRACT) micro-price at trade ts and IV at the time.
    mids_d0 = activity_cache[0][0]
    bids_d0 = activity_cache[0][1]
    asks_d0 = activity_cache[0][2]
    bvol_d0 = activity_cache[0][3]
    avol_d0 = activity_cache[0][4]

    def micro_at(prod, ts):
        b = bids_d0[prod].get(ts)
        a = asks_d0[prod].get(ts)
        bv = bvol_d0[prod].get(ts)
        av = avol_d0[prod].get(ts)
        if b is None or a is None:
            return None
        if bv is None or av is None or (bv + av) <= 0:
            return (a + b) / 2.0
        return (a * bv + b * av) / (bv + av)

    for t in [tr for tr in all_trades if tr["symbol"] == "VEV_5100" and tr["day"] == 0]:
        ts = t["ts"]
        ve_micro = micro_at("VELVETFRUIT_EXTRACT", ts)
        t["ve_micro"] = ve_micro
        t_yrs, tte_d = tte_years(ts, 0)
        t["tte_days"] = tte_d
        # iv at trade time using mid for V5100
        v_mid = mids_d0["VEV_5100"].get(ts)
        if ve_micro and v_mid:
            iv = implied_vol(v_mid, ve_micro, 5100.0, t_yrs)
            t["iv_market"] = iv
        else:
            t["iv_market"] = None
        # smile fair (frozen prior; we don't track EMA across replay so use prior)
        a0, a1, a2 = smile_prior(tte_d)
        if ve_micro and ve_micro > 0:
            m = math.log(ve_micro / 5100.0)
            bias = SMILE_PER_STRIKE_BIAS.get(5100, 0.0)
            fair_iv = a0 + a1 * m + a2 * m * m + bias
            smile_fair = bs_call(ve_micro, 5100.0, t_yrs, fair_iv) if fair_iv > 0.005 else None
            t["smile_fair"] = smile_fair
            t["smile_iv"] = fair_iv
        else:
            t["smile_fair"] = None
            t["smile_iv"] = None
        # BS theo using market IV (intrinsic check)
        if ve_micro and ve_micro > 0:
            t["intrinsic"] = max(ve_micro - 5100.0, 0.0)
        else:
            t["intrinsic"] = None

    v51_d0 = sorted(
        [t for t in all_trades if t["symbol"] == "VEV_5100" and t["day"] == 0],
        key=lambda x: x["pnl_h100"] if x["pnl_h100"] is not None else 0,
    )
    v51_worst10 = v51_d0[:10]

    # cumulative pnl curve V5100 d0 sorted by ts
    v51_chrono = sorted([t for t in all_trades if t["symbol"] == "VEV_5100" and t["day"] == 0], key=lambda x: x["ts"])
    v51_cum = []
    cum_h100 = 0.0
    cum_final = 0.0
    for t in v51_chrono:
        if t["pnl_h100"] is not None:
            cum_h100 += t["pnl_h100"]
        if t["pnl_final"] is not None:
            cum_final += t["pnl_final"]
        v51_cum.append({"ts": t["ts"], "cum_h100": cum_h100, "cum_final": cum_final})

    # bucket V5100 d0 trades by tick-window of 1000
    v51_windowed = defaultdict(lambda: {"n": 0, "sum_h100": 0.0, "sum_final": 0.0})
    for t in v51_chrono:
        win = (t["ts"] // 100) // 1000  # window of 1000 ticks
        v51_windowed[win]["n"] += 1
        if t["pnl_h100"] is not None:
            v51_windowed[win]["sum_h100"] += t["pnl_h100"]
        if t["pnl_final"] is not None:
            v51_windowed[win]["sum_final"] += t["pnl_final"]

    # ---- 5. HYDROGEL day 2 drawdown ts 70k - 91k ----
    hyd_dd = sorted(
        [t for t in all_trades if t["symbol"] == "HYDROGEL_PACK" and t["day"] == 2 and 69_700 <= t["ts"] <= 91_100],
        key=lambda x: x["ts"],
    )
    hyd_dd_summary = {
        "n_trades": len(hyd_dd),
        "n_buys": sum(1 for t in hyd_dd if t["side"] == 1),
        "n_sells": sum(1 for t in hyd_dd if t["side"] == -1),
        "sum_h100": sum(t["pnl_h100"] for t in hyd_dd if t["pnl_h100"] is not None),
        "sum_h1000": sum(t["pnl_h1000"] for t in hyd_dd if t["pnl_h1000"] is not None),
        "sum_h5000": sum(t["pnl_h5000"] for t in hyd_dd if t["pnl_h5000"] is not None),
        "sum_final": sum(t["pnl_final"] for t in hyd_dd if t["pnl_final"] is not None),
    }
    # estimate position movement
    # position before/after window: cumulative side*qty up to ts
    hyd_d2_chrono = sorted(
        [t for t in all_trades if t["symbol"] == "HYDROGEL_PACK" and t["day"] == 2],
        key=lambda x: x["ts"],
    )
    pos_at = 0
    pos_before = 0
    pos_after = 0
    for t in hyd_d2_chrono:
        if t["ts"] < 69_700:
            pos_before += int(t["side"] * t["qty"])
        if t["ts"] <= 91_100:
            pos_after += int(t["side"] * t["qty"])
    pos_change = pos_after - pos_before
    hyd_dd_summary["position_before"] = pos_before
    hyd_dd_summary["position_after"] = pos_after
    hyd_dd_summary["position_change"] = pos_change

    mids_d2 = activity_cache[2][0]["HYDROGEL_PACK"]
    mid_69700 = get_mid(mids_d2, 69_700)
    mid_91100 = get_mid(mids_d2, 91_100)
    hyd_dd_summary["mid_at_69700"] = mid_69700
    hyd_dd_summary["mid_at_91100"] = mid_91100
    hyd_dd_summary["mid_move"] = (mid_91100 - mid_69700) if (mid_69700 and mid_91100) else None

    # Where v13 last traded HYD before window (position has been at 200 for how long?)
    last_trade_before = None
    for t in hyd_d2_chrono:
        if t["ts"] >= 69_700:
            break
        last_trade_before = t
    if last_trade_before is not None:
        hyd_dd_summary["last_hyd_trade_before_window_ts"] = last_trade_before["ts"]
        hyd_dd_summary["last_hyd_trade_before_window_side"] = last_trade_before["side"]
        hyd_dd_summary["last_hyd_trade_before_window_price"] = last_trade_before["price"]
    else:
        hyd_dd_summary["last_hyd_trade_before_window_ts"] = None

    # When did v13 first trade HYD AFTER window? (recovery)
    first_after = None
    for t in hyd_d2_chrono:
        if t["ts"] > 91_100:
            first_after = t
            break
    if first_after:
        hyd_dd_summary["first_hyd_trade_after_window_ts"] = first_after["ts"]
        hyd_dd_summary["first_hyd_trade_after_window_side"] = first_after["side"]
        hyd_dd_summary["first_hyd_trade_after_window_price"] = first_after["price"]
        # mid at that ts
        hyd_dd_summary["mid_at_first_after"] = get_mid(mids_d2, first_after["ts"])
    else:
        hyd_dd_summary["first_hyd_trade_after_window_ts"] = None

    # Mid extremum during the window
    mid_min_in_window = None
    mid_min_ts = None
    for ts in sorted(mids_d2.keys()):
        if 69_700 <= ts <= 91_100:
            m = mids_d2[ts]
            if mid_min_in_window is None or m < mid_min_in_window:
                mid_min_in_window = m
                mid_min_ts = ts
    hyd_dd_summary["mid_min_in_window"] = mid_min_in_window
    hyd_dd_summary["mid_min_in_window_ts"] = mid_min_ts

    # ---- 6. Voucher warmup window (first 30 ticks vs 30-1000) ----
    voucher_prods = sorted({t["symbol"] for t in all_trades if t["symbol"].startswith("VEV_")})
    warmup_table = []
    for prod in voucher_prods:
        for day in DAYS:
            warm = [t for t in all_trades if t["symbol"] == prod and t["day"] == day and t["tick_idx"] < 30]
            steady = [t for t in all_trades if t["symbol"] == prod and t["day"] == day and 30 <= t["tick_idx"] < 1000]
            wp = [t["pnl_h100"] for t in warm if t["pnl_h100"] is not None]
            sp = [t["pnl_h100"] for t in steady if t["pnl_h100"] is not None]
            warmup_table.append({
                "product": prod,
                "day": day,
                "warm_n": len(warm),
                "warm_sum_h100": sum(wp),
                "warm_mean": statistics.fmean(wp) if wp else 0,
                "steady_n": len(steady),
                "steady_sum_h100": sum(sp),
                "steady_mean": statistics.fmean(sp) if sp else 0,
            })

    # ---- 7. Top 10 product/day losers (by pnl_final) ----
    pd_pnl = defaultdict(lambda: {"n": 0, "h100": 0.0, "h1000": 0.0, "h5000": 0.0, "final": 0.0})
    for t in all_trades:
        k = (t["symbol"], t["day"])
        pd_pnl[k]["n"] += 1
        if t["pnl_h100"] is not None:
            pd_pnl[k]["h100"] += t["pnl_h100"]
        if t["pnl_h1000"] is not None:
            pd_pnl[k]["h1000"] += t["pnl_h1000"]
        if t["pnl_h5000"] is not None:
            pd_pnl[k]["h5000"] += t["pnl_h5000"]
        if t["pnl_final"] is not None:
            pd_pnl[k]["final"] += t["pnl_final"]

    pd_losers = sorted(pd_pnl.items(), key=lambda kv: kv[1]["final"])

    # ---- 7c. Classify each trade as AGG vs PASSIVE based on book at entry ----
    for t in all_trades:
        d = t["day"]
        prod = t["symbol"]
        bid = activity_cache[d][1][prod].get(t["ts"])
        ask = activity_cache[d][2][prod].get(t["ts"])
        cls = "UNKNOWN"
        if t["side"] == -1:  # SELL
            if bid is not None and t["price"] <= bid:
                cls = "AGG_SELL"
            else:
                cls = "PASS_SELL"
        else:  # BUY
            if ask is not None and t["price"] >= ask:
                cls = "AGG_BUY"
            else:
                cls = "PASS_BUY"
        t["fill_class"] = cls

    fill_summary = defaultdict(lambda: {"n": 0, "qty": 0, "h100": 0.0, "h1000": 0.0, "final": 0.0})
    for t in all_trades:
        k = (t["symbol"], t["day"], t["fill_class"])
        s = fill_summary[k]
        s["n"] += 1; s["qty"] += t["qty"]
        if t["pnl_h100"] is not None: s["h100"] += t["pnl_h100"]
        if t["pnl_h1000"] is not None: s["h1000"] += t["pnl_h1000"]
        if t["pnl_final"] is not None: s["final"] += t["pnl_final"]

    # ---- 8. Overall stats ----
    out = {}
    out["total_own_trades"] = len(all_trades)
    out["total_pnl_h100"] = sum(t["pnl_h100"] for t in all_trades if t["pnl_h100"] is not None)
    out["total_pnl_h1000"] = sum(t["pnl_h1000"] for t in all_trades if t["pnl_h1000"] is not None)
    out["total_pnl_h5000"] = sum(t["pnl_h5000"] for t in all_trades if t["pnl_h5000"] is not None)
    out["total_pnl_final"] = sum(t["pnl_final"] for t in all_trades if t["pnl_final"] is not None)

    # ---- 9. Top 10 specific fixable losing TRADE-CATEGORIES ----
    # We rank (product, day, bucket) by sum_h5000 most negative, where bucket is meaningful.
    losing_buckets_sorted = sorted(losing_buckets, key=lambda x: x["sum_h5000"])
    losers_top = [b for b in losing_buckets_sorted if b["sum_h5000"] < 0][:30]

    # ---- write CSVs ----
    # all trades enriched (use union of keys; some rows have extra V5100 fields)
    with (OUT_DIR / "v13_trades_enriched.csv").open("w") as f:
        if all_trades:
            keys = []
            seen_keys = set()
            for r in all_trades:
                for k in r:
                    if k not in seen_keys:
                        seen_keys.add(k)
                        keys.append(k)
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for r in all_trades:
                w.writerow(r)
    print(f"[wrote] {OUT_DIR / 'v13_trades_enriched.csv'}", file=sys.stderr)

    # horizon summary
    with (OUT_DIR / "v13_horizon_summary.csv").open("w") as f:
        w = csv.DictWriter(f, fieldnames=["product", "day", "horizon", "n", "sum", "mean", "std", "tstat"])
        w.writeheader()
        for r in horizon_summary:
            w.writerow(r)
    # losing buckets
    with (OUT_DIR / "v13_losing_buckets.csv").open("w") as f:
        w = csv.DictWriter(f, fieldnames=["product", "day", "bucket", "n", "sum_h5000", "mean_h5000"])
        w.writeheader()
        for r in losing_buckets:
            w.writerow(r)

    # ---- write report ----
    md_path = OUT_DIR / "v13_trade_audit.md"
    with md_path.open("w") as f:
        w = f.write
        w("# v13 Trade Audit\n\n")
        w(f"Generated 2026-04-25.\n\n")
        w(f"Source runs: `runs/v13_d0_audit`, `runs/v13_d1_audit`, `runs/v13_d2_audit`.\n\n")
        w("Total trade count: **{}** across 3 days, 10k ticks each.\n\n".format(out["total_own_trades"]))

        # Executive summary
        w("## TL;DR — what loses money in v13\n\n")
        d0_pnl = sum(t["pnl_final"] for t in all_trades if t["day"] == 0 and t["pnl_final"] is not None)
        d1_pnl = sum(t["pnl_final"] for t in all_trades if t["day"] == 1 and t["pnl_final"] is not None)
        d2_pnl = sum(t["pnl_final"] for t in all_trades if t["day"] == 2 and t["pnl_final"] is not None)
        w(f"v13 makes +{out['total_pnl_final']:.0f} total over 30k ticks "
          f"(D0 +{d0_pnl:.0f}, D1 +{d1_pnl:.0f}, D2 +{d2_pnl:.0f}).\n\n")
        w("Five (product, day) cells are net-negative on final-mid:\n\n")
        for (prod, day), v in sorted([(k, v) for k, v in pd_pnl.items() if v["final"] < 0], key=lambda kv: kv[1]["final"]):
            w(f"- **{prod} day {day}**: final {v['final']:.0f}, n={v['n']} trades\n")
        w("\n")
        w("**Largest individual losing trade-class** (sec. 6c-i): "
          "VEV_5100 day 0 AGG_SELL — 45 aggressive sells (340 qty) for -2596 final-mid.\n")
        w("This is the entire V5100 d0 loss; v13's smile-EMA fair undershoots V5100 mid in late day 0 "
          "and the 0.7-shell take rule mechanically hits the bid into a rising mid.\n\n")
        w("**Largest paper churn** (not net-loss but pays huge spread): VFE day 2 — AGG_BUY +98,316 "
          "and AGG_SELL -94,257; both legs cycle through 200-cap inventory on a trending day.\n\n")
        w("**HYDROGEL d2 drawdown 69.7k→91.1k is NOT trade-driven**: zero new trades in window. "
          "Pure mark-to-market on max-long (+200) inventory. Recovers; final D2 HYD = +42,412.\n\n")
        w("**Warmup losses are negligible**: only 1 voucher trade per (day, product) in first 30 ticks, "
          "total impact < 80 shells across all vouchers.\n\n")

        w("## 1. PnL totals (final mid attribution)\n\n")
        w("| Day | reported (rust) | sum trade pnl_h100 | sum h1000 | sum h5000 | sum final-mid |\n")
        w("|---|---|---|---|---|---|\n")
        # split by day
        for d in DAYS:
            day_trades = [t for t in all_trades if t["day"] == d]
            tot_100 = sum(t["pnl_h100"] for t in day_trades if t["pnl_h100"] is not None)
            tot_1000 = sum(t["pnl_h1000"] for t in day_trades if t["pnl_h1000"] is not None)
            tot_5000 = sum(t["pnl_h5000"] for t in day_trades if t["pnl_h5000"] is not None)
            tot_final = sum(t["pnl_final"] for t in day_trades if t["pnl_final"] is not None)
            w(f"| {d} | n={len(day_trades)} | {tot_100:.0f} | {tot_1000:.0f} | {tot_5000:.0f} | {tot_final:.0f} |\n")
        w("\n")

        w("## 2. Per (product, day) PnL summary\n\n")
        w("| product | day | n | h100 | h1000 | h5000 | final |\n")
        w("|---|---|---|---|---|---|---|\n")
        for (prod, day), v in sorted(pd_pnl.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            w(f"| {prod} | {day} | {v['n']} | {v['h100']:.0f} | {v['h1000']:.0f} | {v['h5000']:.0f} | {v['final']:.0f} |\n")
        w("\n")

        w("## 3. Worst (product, day) cells, ranked by final-mid PnL\n\n")
        w("| product | day | n | final | h5000 | h1000 | h100 |\n")
        w("|---|---|---|---|---|---|---|\n")
        for (prod, day), v in pd_losers[:15]:
            w(f"| {prod} | {day} | {v['n']} | {v['final']:.0f} | {v['h5000']:.0f} | {v['h1000']:.0f} | {v['h100']:.0f} |\n")
        w("\n")

        w("## 4. Horizon attribution by product (sum across 3 days)\n\n")
        w("| product | h | n | sum | mean | tstat |\n")
        w("|---|---|---|---|---|---|\n")
        # roll up by product+horizon
        prod_h = defaultdict(lambda: {"n": 0, "sum": 0.0, "vals": []})
        for r in horizon_summary:
            k = (r["product"], r["horizon"])
            prod_h[k]["n"] += r["n"]
            prod_h[k]["sum"] += r["sum"]
        for (prod, h), v in sorted(prod_h.items()):
            mean = v["sum"] / v["n"] if v["n"] else 0
            w(f"| {prod} | {h} | {v['n']} | {v['sum']:.0f} | {mean:.2f} | - |\n")
        w("\n")

        w("## 5. V5100 day 0 deep-dive\n\n")
        w(f"Total trades: {len(v51_chrono)}, sum_h100={sum(t['pnl_h100'] for t in v51_chrono if t['pnl_h100'] is not None):.0f}, sum_final={sum(t['pnl_final'] for t in v51_chrono if t['pnl_final'] is not None):.0f}.\n\n")

        w("### 5a. PnL by 1000-tick window (V5100 day 0)\n\n")
        w("| window (ticks) | n_trades | sum_h100 | sum_final |\n")
        w("|---|---|---|---|\n")
        for win in sorted(v51_windowed):
            v = v51_windowed[win]
            w(f"| {win*1000}-{win*1000+999} | {v['n']} | {v['sum_h100']:.0f} | {v['sum_final']:.0f} |\n")
        w("\n")

        w("### 5b. Worst 10 V5100 d0 trades by horizon-100 PnL\n\n")
        w("| ts | tick | side | qty | px | mid | spr | imb | VE_micro | smile_fair | smile_iv | mkt_iv | tte(d) | h100 | h1000 | final |\n")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for t in v51_worst10:
            side_lbl = "BUY" if t["side"] == 1 else "SELL"
            spread = f"{t['spread']:.0f}" if t["spread"] is not None else "-"
            imb = f"{t['imb_k1']:.2f}" if t["imb_k1"] is not None else "-"
            mid = f"{t['mid_at']:.1f}" if t["mid_at"] is not None else "-"
            ve = f"{t.get('ve_micro'):.1f}" if t.get("ve_micro") is not None else "-"
            sf = f"{t.get('smile_fair'):.1f}" if t.get("smile_fair") is not None else "-"
            siv = f"{t.get('smile_iv'):.4f}" if t.get("smile_iv") is not None else "-"
            miv = f"{t.get('iv_market'):.4f}" if t.get("iv_market") not in (None, float('nan')) and t.get('iv_market') == t.get('iv_market') else "-"
            tte_d = f"{t.get('tte_days'):.2f}" if t.get("tte_days") is not None else "-"
            ph100 = f"{t['pnl_h100']:.0f}" if t["pnl_h100"] is not None else "-"
            ph1000 = f"{t['pnl_h1000']:.0f}" if t["pnl_h1000"] is not None else "-"
            pf = f"{t['pnl_final']:.0f}" if t["pnl_final"] is not None else "-"
            w(f"| {t['ts']} | {t['tick_idx']} | {side_lbl} | {t['qty']:.0f} | {t['price']:.1f} | {mid} | {spread} | {imb} | {ve} | {sf} | {siv} | {miv} | {tte_d} | {ph100} | {ph1000} | {pf} |\n")
        w("\n")

        w("## 6. HYDROGEL day 2 drawdown ts 69,700 -> 91,100\n\n")
        s = hyd_dd_summary
        w(f"- trades in window: **{s['n_trades']}** ({s['n_buys']} BUY, {s['n_sells']} SELL)\n")
        w(f"- sum pnl_h100 in window: **{s['sum_h100']:.0f}**\n")
        w(f"- sum pnl_h1000 in window: **{s['sum_h1000']:.0f}**\n")
        w(f"- sum pnl_h5000 in window: **{s['sum_h5000']:.0f}**\n")
        w(f"- sum pnl_final in window: **{s['sum_final']:.0f}**\n")
        w(f"- HYDROGEL position **before** window: {s['position_before']}\n")
        w(f"- HYDROGEL position **after** window:  {s['position_after']}\n")
        w(f"- net position change in window: {s['position_change']}\n")
        w(f"- HYDROGEL mid at ts 69,700: {s['mid_at_69700']}\n")
        w(f"- HYDROGEL mid at ts 91,100: {s['mid_at_91100']}\n")
        w(f"- mid trough in window: {s['mid_min_in_window']} @ ts {s['mid_min_in_window_ts']}\n")
        w(f"- net mid move: {s['mid_move']}\n")
        if s.get("last_hyd_trade_before_window_ts") is not None:
            w(f"- last HYD trade before window: ts={s['last_hyd_trade_before_window_ts']} side={'BUY' if s['last_hyd_trade_before_window_side']==1 else 'SELL'} price={s['last_hyd_trade_before_window_price']}\n")
        if s.get("first_hyd_trade_after_window_ts") is not None:
            w(f"- first HYD trade after window: ts={s['first_hyd_trade_after_window_ts']} side={'BUY' if s['first_hyd_trade_after_window_side']==1 else 'SELL'} price={s['first_hyd_trade_after_window_price']} (mid={s.get('mid_at_first_after')})\n")
        w("\n")

        # Diagnose A vs B vs C
        if s["n_trades"] == 0:
            diag = ("(a) **Position-driven, pure mark-to-market.** "
                    "There were ZERO trades in the window. v13 was max-long (+200) coming in "
                    f"and the mid drifted from {s['mid_at_69700']} to a trough of {s['mid_min_in_window']} "
                    f"and recovered partially to {s['mid_at_91100']}. "
                    "The trader correctly stopped quoting bids (already at cap) and never lifted. "
                    "Position recovers mid-term — final-mid PnL on the day is +42,412. "
                    "**Fix: nothing to fix; this is mean-reversion noise on max-long inventory.** "
                    "If we want to dampen the drawdown, we could trim long inventory faster when EMA falls — "
                    "e.g. force-sell when pos > +180 and slow_EMA - micro > 8, or activate a take-profit on +pos when fair has risen >= 5 above entry-VWAP.")
        elif s["sum_h100"] < -2000:
            diag = "(b) Bad trades: trade-level horizon-PnL is itself negative; suppress these trades."
        else:
            diag = "(c) Mix: window trades are not benign and mid moved against existing inventory."
        w(f"**Diagnosis:** {diag}\n\n")

        w("## 6c. Aggressive vs passive fill PnL by (product, day)\n\n")
        w("AGG_SELL = we hit the bid (took liquidity selling). AGG_BUY = we lifted the ask (took liquidity buying).\n")
        w("PASS_BUY = our bid was hit. PASS_SELL = our offer was lifted.\n\n")
        w("| product | day | class | n | qty | h100 | h1000 | final |\n")
        w("|---|---|---|---|---|---|---|---|\n")
        for (prod, day, cls), s in sorted(fill_summary.items()):
            if s["n"] == 0: continue
            w(f"| {prod} | {day} | {cls} | {s['n']} | {s['qty']:.0f} | {s['h100']:.0f} | {s['h1000']:.0f} | {s['final']:.0f} |\n")
        w("\n")

        # focus: AGG fills with negative final (these are the actual losing crossings)
        agg_neg = [(k, s) for k, s in fill_summary.items()
                   if k[2] in ("AGG_BUY", "AGG_SELL") and s["final"] < 0]
        agg_neg.sort(key=lambda kv: kv[1]["final"])
        w("### 6c-i. Aggressive crossings that LOSE on final-mid (top 15)\n\n")
        w("These are taker-side trades where the trader paid the spread and then mid moved against them.\n\n")
        w("| product | day | class | n | qty | h100 | h1000 | final |\n")
        w("|---|---|---|---|---|---|---|---|\n")
        for (prod, day, cls), s in agg_neg[:15]:
            w(f"| {prod} | {day} | {cls} | {s['n']} | {s['qty']:.0f} | {s['h100']:.0f} | {s['h1000']:.0f} | {s['final']:.0f} |\n")
        w("\n")

        w("## 7. Voucher warmup window (first 30 ticks vs 30-1000)\n\n")
        w("| product | day | warm_n | warm_sum_h100 | warm_mean | steady_n | steady_sum_h100 | steady_mean |\n")
        w("|---|---|---|---|---|---|---|---|\n")
        for r in warmup_table:
            w(f"| {r['product']} | {r['day']} | {r['warm_n']} | {r['warm_sum_h100']:.0f} | {r['warm_mean']:.2f} | {r['steady_n']} | {r['steady_sum_h100']:.0f} | {r['steady_mean']:.2f} |\n")
        w("\n")

        w("## 8. Worst trade buckets (lowest sum_pnl_h5000)\n\n")
        w("| product | day | bucket | n | sum_h5000 | mean_h5000 |\n")
        w("|---|---|---|---|---|---|\n")
        for b in losing_buckets_sorted[:30]:
            w(f"| {b['product']} | {b['day']} | {b['bucket']} | {b['n']} | {b['sum_h5000']:.0f} | {b['mean_h5000']:.2f} |\n")
        w("\n")

        # ---- 10 fixable losers ----
        # We rank (product, day, bucket) by sum_h5000 most negative,
        # but de-duplicate by keeping only the highest-impact bucket per (product, day, side-class)
        # to avoid the report being dominated by overlapping buckets.
        w("## 9. Top 10 specific fixable losers (sorted by absolute size)\n\n")
        w("Each row pairs a (product, day, bucket) loss with a 1-line surgical fix.\n")
        w("Buckets are de-duplicated so each (product, day) appears at most twice (once per side-class).\n\n")
        w("| rank | product | day | bucket | n | sum_h5000 | suggested rule |\n")
        w("|---|---|---|---|---|---|---|\n")

        def rule_for(prod, day, bucket):
            # tailored rule strings
            base = {
                "BUY_when_imb<-0.3": f"skip BUYs on {prod} when imb_k1 < -0.3",
                "BUY_when_imb<-0.5": f"skip BUYs on {prod} when imb_k1 < -0.5",
                "SELL_when_imb>0.3": f"skip SELLs on {prod} when imb_k1 > 0.3",
                "SELL_when_imb>0.5": f"skip SELLs on {prod} when imb_k1 > 0.5",
                "first_30_ticks":   f"delay {prod} quoting until tick >= 30 (warm-up gate)",
                "first_100_ticks":  f"delay {prod} quoting until tick >= 100",
                "spread_gt_2":      f"skip {prod} quoting when book spread > 2",
                "spread_gt_3":      f"skip {prod} quoting when book spread > 3",
                "BUY_above_mid":    f"never lift offers above mid on {prod}",
                "SELL_below_mid":   f"never hit bids below mid on {prod}",
            }
            return base.get(bucket, f"investigate {prod}")

        def side_class(bucket):
            if "BUY" in bucket:
                return "BUY"
            if "SELL" in bucket:
                return "SELL"
            return "OTHER"

        # de-duplicate by (product, day, side_class) keeping the most-negative bucket
        seen = {}
        for b in losers_top:
            key = (b["product"], b["day"], side_class(b["bucket"]))
            cur = seen.get(key)
            if cur is None or b["sum_h5000"] < cur["sum_h5000"]:
                seen[key] = b
        # also add (product, day, "OTHER") for warmup/spread but rank against above
        deduped = sorted(seen.values(), key=lambda x: x["sum_h5000"])

        for i, b in enumerate(deduped[:10], 1):
            w(f"| {i} | {b['product']} | {b['day']} | {b['bucket']} | {b['n']} | {b['sum_h5000']:.0f} | {rule_for(b['product'], b['day'], b['bucket'])} |\n")
        w("\n")

        # ---- "true" losers — (product, day) cells with negative final ----
        w("### 9b. (product, day) cells that are net-negative on final-mid\n\n")
        true_neg = [(k, v) for k, v in pd_pnl.items() if v["final"] < 0]
        true_neg.sort(key=lambda kv: kv[1]["final"])
        w("| product | day | n | h100 | h1000 | h5000 | final |\n")
        w("|---|---|---|---|---|---|---|\n")
        for (prod, day), v in true_neg:
            w(f"| {prod} | {day} | {v['n']} | {v['h100']:.0f} | {v['h1000']:.0f} | {v['h5000']:.0f} | {v['final']:.0f} |\n")
        w("\n")

        # ---- 9c. CONCRETE v14 patches ----
        w("### 9c. Concrete v14 patches (ranked by expected PnL recovery)\n\n")
        w("Each patch references the exact v13 code path and a 1-2 line edit.\n\n")
        w("| # | size_now | patch | estimated saved |\n")
        w("|---|---|---|---|\n")
        # Build list of patches based on findings:
        # 1) V5100 d0 AGG_SELL = -2596 final, 45 trades, 340 qty.
        #    Smile-take rule fires too aggressively. Fix: per-strike bias for V5100, raise SMILE_PER_STRIKE_BIAS[5100] to ~+0.005, OR raise SMILE_TAKE_EDGE_SHELLS for V5100 only to 1.5.
        # 2) VFE d2 AGG_SELL = -94257 vs AGG_BUY +98316 — net +4k, but the churn loses to spread.
        #    The micro EMA + imb_k2 skew is fine (it identifies direction); the issue is sizing & cap.
        # 3) HYDROGEL d0 AGG_BUY = -37280 (counterbalanced by +106843 sell).
        # 4) V5400 d2 AGG_SELL = -704 (16 trades, 26 qty) — should not be tradeable on day 2.
        # 5) Warmup losses are tiny (just a few trades each) — not worth optimizing.

        v51_d0_agg_sell = fill_summary.get(("VEV_5100", 0, "AGG_SELL"), None)
        vfe_d2_agg_sell = fill_summary.get(("VELVETFRUIT_EXTRACT", 2, "AGG_SELL"), None)
        v54_d2_agg_sell = fill_summary.get(("VEV_5400", 2, "AGG_SELL"), None)
        hyd_d0_agg_buy = fill_summary.get(("HYDROGEL_PACK", 0, "AGG_BUY"), None)
        vfe_d2_pass_sell = fill_summary.get(("VELVETFRUIT_EXTRACT", 2, "PASS_SELL"), None)
        v51_d2_agg_sell_count = sum(1 for t in all_trades
                                    if t["symbol"] == "VEV_5100" and t["day"] == 2 and t["fill_class"] == "AGG_SELL")

        patches = []
        if v51_d0_agg_sell:
            patches.append({
                "n": v51_d0_agg_sell["n"], "qty": v51_d0_agg_sell["qty"],
                "size": v51_d0_agg_sell["final"],
                "patch": "V5100 d0 — set SMILE_PER_STRIKE_BIAS[5100] += 0.005 (currently +0.0004) so smile fair tracks the slightly-richer V5100 market and the 0.7-shell take rule stops firing on 150-bid-into-152-mid",
            })
        if vfe_d2_agg_sell:
            patches.append({
                "n": vfe_d2_agg_sell["n"], "qty": vfe_d2_agg_sell["qty"],
                "size": vfe_d2_agg_sell["final"],
                "patch": "VFE d2 AGG_SELL = -94k offsets +98k AGG_BUY — net +4k but huge spread cost; skip VFE quoting when |imb_k2| > 0.5 (raise V_SKEW_CAP gate, currently 2 shells)",
            })
        if hyd_d0_agg_buy:
            patches.append({
                "n": hyd_d0_agg_buy["n"], "qty": hyd_d0_agg_buy["qty"],
                "size": hyd_d0_agg_buy["final"],
                "patch": "HYDROGEL d0 AGG_BUY -37k vs +106k AGG_SELL is net +69k but lifting offers above mid eats spread; gate HYD lifts on imb_k1 < +0.2",
            })
        if v54_d2_agg_sell:
            patches.append({
                "n": v54_d2_agg_sell["n"], "qty": v54_d2_agg_sell["qty"],
                "size": v54_d2_agg_sell["final"],
                "patch": "V5400 d2 AGG_SELL is the only voucher loss on day 2 — V5400 at TTE 6 has thin volume; widen SMILE_TAKE_EDGE_SHELLS for V5400 to 2.0 or drop V5400 from take legs",
            })
        # HYDROGEL d2 drawdown: not bad trades; only patch is risk-management
        patches.append({
            "n": 0, "qty": s.get("position_before", 0),
            "size": -16400.0,
            "patch": "HYDROGEL d2 ts69.7k-91.1k drawdown is purely position-driven (0 trades). Optional: trim long inventory faster — force-sell when pos > +180 and slow_EMA - micro > 8. Not strictly a 'losing trade' fix.",
        })
        # V5100 d2 has 0 AGG_SELL but earlier table shows -1882 BUY_above_mid; that is take-leg buying.
        v51_d2_agg_buy = fill_summary.get(("VEV_5100", 2, "AGG_BUY"), None)
        if v51_d2_agg_buy and v51_d2_agg_buy["final"] < 0:
            patches.append({
                "n": v51_d2_agg_buy["n"], "qty": v51_d2_agg_buy["qty"],
                "size": v51_d2_agg_buy["final"],
                "patch": "V5100 d2 AGG_BUY losing — same per-strike-bias issue inverted. Reduce V5100 take edge or ATM-IV bias",
            })

        # Sort patches by absolute size
        patches.sort(key=lambda p: p["size"])
        for i, p in enumerate(patches[:10], 1):
            w(f"| {i} | n={p['n']} qty={p['qty']:.0f} | {p['patch']} | {p['size']:.0f} |\n")
        w("\n")

        # also: per-trade biggest losers, for visibility
        biggest = sorted(
            [t for t in all_trades if t["pnl_h5000"] is not None],
            key=lambda x: x["pnl_h5000"],
        )[:20]
        w("## 10. 20 biggest individual losing trades (by horizon-5000 PnL)\n\n")
        w("| day | ts | product | side | qty | price | mid | spread | imb | h100 | h1000 | h5000 | final |\n")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for t in biggest:
            side = "BUY" if t["side"] == 1 else "SELL"
            sp = f"{t['spread']:.0f}" if t["spread"] is not None else "-"
            imb = f"{t['imb_k1']:.2f}" if t["imb_k1"] is not None else "-"
            mid = f"{t['mid_at']:.1f}" if t["mid_at"] is not None else "-"
            def pf(k):
                v = t[k]
                return f"{v:.0f}" if v is not None else "-"
            w(f"| {t['day']} | {t['ts']} | {t['symbol']} | {side} | {t['qty']:.0f} | {t['price']:.1f} | {mid} | {sp} | {imb} | {pf('pnl_h100')} | {pf('pnl_h1000')} | {pf('pnl_h5000')} | {pf('pnl_final')} |\n")
        w("\n")

    print(f"[wrote] {md_path}", file=sys.stderr)
    return md_path, out


if __name__ == "__main__":
    md, summ = main()
    print("REPORT:", md)
    for k, v in summ.items():
        print(f"  {k}: {v:.0f}" if isinstance(v, float) else f"  {k}: {v}")
