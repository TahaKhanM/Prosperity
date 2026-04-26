"""Deep replay analysis of v10 vs v9 across day 0/1/2.

Outputs PNG figures + per-product trade attribution to identify
inefficiencies that v11 should target.
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path("/Users/tahakhan/Documents/Work/Projects/Prosperity")
OUT = ROOT / "prosperity-research" / "05_v10_replay_analysis"
RUST = ROOT / "prosperity_rust_backtester"

V10 = {0: "backtest-1777111909481", 1: "backtest-1777111911593", 2: "backtest-1777111882024"}
V9 = {0: "backtest-1777111896208", 1: "backtest-1777111898318", 2: "backtest-1777111901405"}


def read_trades(rundir):
    p = RUST / "runs" / rundir / "trades.csv"
    out = []
    with open(p) as f:
        r = csv.DictReader(f, delimiter=";")
        for row in r:
            buyer = row["buyer"] or ""
            seller = row["seller"] or ""
            sym = row["symbol"]
            qty = int(row["quantity"])
            price = float(row["price"])
            ts = int(row["timestamp"])
            # SUBMISSION = us
            if buyer == "SUBMISSION":
                side = +1
            elif seller == "SUBMISSION":
                side = -1
            else:
                continue  # market trade
            out.append((ts, sym, side, qty, price))
    return out


def read_activity(rundir):
    """Returns dict[symbol] -> list of (ts, b1, bv1, a1, av1, mid)."""
    p = RUST / "runs" / rundir / "activity.csv"
    out = defaultdict(list)
    with open(p) as f:
        r = csv.DictReader(f, delimiter=";")
        for row in r:
            sym = row["product"]
            ts = int(row["timestamp"])
            mid = float(row["mid_price"]) if row["mid_price"] else None
            b1 = float(row["bid_price_1"]) if row["bid_price_1"] else None
            a1 = float(row["ask_price_1"]) if row["ask_price_1"] else None
            bv1 = float(row["bid_volume_1"]) if row["bid_volume_1"] else None
            av1 = float(row["ask_volume_1"]) if row["ask_volume_1"] else None
            out[sym].append((ts, b1, bv1, a1, av1, mid))
    return out


def read_pnl(rundir):
    p = RUST / "runs" / rundir / "pnl_by_product.csv"
    rows = []
    with open(p) as f:
        r = csv.DictReader(f, delimiter=";")
        for row in r:
            rows.append({k: float(v) if v else 0 for k, v in row.items()})
    return rows


def per_trade_pnl(trades, mids_by_sym):
    """For each our-trade, compute attributable PnL = qty*side*(future_mid - price)
    over multiple horizons. Future mid taken from the matching activity timestep
    that follows. Returns list of (ts, sym, side, qty, price, pnl_h1, pnl_h10, pnl_h100)
    """
    out = []
    # build ts->mid lookup
    lookup = {}
    for sym, rows in mids_by_sym.items():
        d = {ts: m for ts, _, _, _, _, m in rows if m is not None}
        lookup[sym] = d
    horizons = [1, 5, 10, 50, 100]
    for ts, sym, side, qty, price in trades:
        d = lookup.get(sym, {})
        ts_keys = sorted(d.keys())
        # find index >= ts
        try:
            idx = next(i for i, k in enumerate(ts_keys) if k >= ts)
        except StopIteration:
            continue
        pnls = []
        for h in horizons:
            j = idx + h
            if j >= len(ts_keys):
                pnls.append(None)
                continue
            future_mid = d[ts_keys[j]]
            pnls.append(side * qty * (future_mid - price))
        out.append((ts, sym, side, qty, price, pnls))
    return out, horizons


def plot_pnl_curves():
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=False)
    for d, ax in zip((0, 1, 2), axes):
        v9p = read_pnl(V9[d])
        v10p = read_pnl(V10[d])
        ts9 = [r["timestamp"] for r in v9p]
        t9 = [r["total"] for r in v9p]
        ts10 = [r["timestamp"] for r in v10p]
        t10 = [r["total"] for r in v10p]
        ax.plot(ts9, t9, label="v9 total", color="C0", alpha=0.85, lw=1.5)
        ax.plot(ts10, t10, label="v10 total", color="C1", alpha=0.85, lw=1.5)
        ax.set_title(f"Day {d}: cumulative total PnL")
        ax.set_xlabel("timestamp")
        ax.legend(loc="upper left")
        ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT / "pnl_total_curves.png", dpi=120)
    plt.close()


def plot_per_product_pnl():
    fig, axes = plt.subplots(3, 4, figsize=(20, 11))
    for di, d in enumerate((0, 1, 2)):
        v9p = read_pnl(V9[d])
        v10p = read_pnl(V10[d])
        for pi, p in enumerate(["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT",
                                "VEV_5100", "VEV_5300"]):
            ax = axes[di, pi]
            ts = [r["timestamp"] for r in v10p]
            v9 = [r.get(p, 0) for r in v9p]
            v10 = [r.get(p, 0) for r in v10p]
            ax.plot(ts, v9, label="v9", color="C0", alpha=0.85, lw=1.4)
            ax.plot(ts, v10, label="v10", color="C1", alpha=0.85, lw=1.4)
            ax.set_title(f"Day {d}: {p}")
            ax.legend(loc="upper left", fontsize=8)
            ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT / "pnl_per_product.png", dpi=120)
    plt.close()


def plot_voucher_pnl():
    """All voucher strikes day 0/1/2 in a 3x10 grid (overall pnl curve)."""
    strikes = [4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000, 6500]
    fig, axes = plt.subplots(3, 10, figsize=(28, 9))
    for di, d in enumerate((0, 1, 2)):
        v9p = read_pnl(V9[d])
        v10p = read_pnl(V10[d])
        for ki, k in enumerate(strikes):
            ax = axes[di, ki]
            sym = f"VEV_{k}"
            ts = [r["timestamp"] for r in v10p]
            v9v = [r.get(sym, 0) for r in v9p]
            v10v = [r.get(sym, 0) for r in v10p]
            ax.plot(ts, v9v, label="v9", color="C0", alpha=0.85, lw=1.0)
            ax.plot(ts, v10v, label="v10", color="C1", alpha=0.85, lw=1.0)
            ax.set_title(f"D{d} {sym}", fontsize=9)
            ax.tick_params(labelsize=7)
            ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(OUT / "pnl_voucher_grid.png", dpi=110)
    plt.close()


def plot_mids_with_trades(d, sym):
    """Plot mid + our-trades on top, both v9 and v10, day d."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    titles = ["v9", "v10"]
    runs = [V9[d], V10[d]]
    for i, (rdir, title) in enumerate(zip(runs, titles)):
        act = read_activity(rdir)
        rows = act.get(sym, [])
        ts = [r[0] for r in rows]
        mid = [r[5] for r in rows]
        axes[i].plot(ts, mid, color="black", lw=0.8, alpha=0.6, label="mid")
        # add trades
        trades = read_trades(rdir)
        buys_x, buys_y = [], []
        sells_x, sells_y = [], []
        for t_ts, t_sym, t_side, t_qty, t_px in trades:
            if t_sym != sym:
                continue
            if t_side > 0:
                buys_x.append(t_ts); buys_y.append(t_px)
            else:
                sells_x.append(t_ts); sells_y.append(t_px)
        axes[i].scatter(buys_x, buys_y, c="green", s=8, alpha=0.5, label="our buys")
        axes[i].scatter(sells_x, sells_y, c="red", s=8, alpha=0.5, label="our sells")
        axes[i].set_title(f"Day {d} {sym} — {title}")
        axes[i].legend(loc="upper left", fontsize=8)
        axes[i].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT / f"mids_trades_d{d}_{sym}.png", dpi=110)
    plt.close()


def plot_position_curves(d, sym):
    """Track running position over time."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
    for i, (rdir, title) in enumerate([(V9[d], "v9"), (V10[d], "v10")]):
        trades = read_trades(rdir)
        # filter to sym
        trs = [(t[0], t[2] * t[3]) for t in trades if t[1] == sym]
        trs.sort()
        ts_ = [t[0] for t in trs]
        pos = []
        cur = 0
        for _, q in trs:
            cur += q
            pos.append(cur)
        axes[i].plot(ts_, pos, lw=0.8)
        axes[i].set_title(f"Day {d} {sym} position over time — {title}")
        axes[i].grid(alpha=0.3)
        axes[i].axhline(0, color="black", lw=0.4)
    plt.tight_layout()
    plt.savefig(OUT / f"position_d{d}_{sym}.png", dpi=110)
    plt.close()


def attribute_per_trade(d, version="v10"):
    """For every our-trade, compute future-realized horizon PnL."""
    rdir = (V10 if version == "v10" else V9)[d]
    trades = read_trades(rdir)
    mids = read_activity(rdir)
    pnls, horizons = per_trade_pnl(trades, mids)
    # aggregate per (sym, side)
    agg = defaultdict(lambda: [0]*len(horizons) + [0])  # [sum_h1, sum_h5,..., n]
    for ts, sym, side, qty, price, pls in pnls:
        for i, p in enumerate(pls):
            if p is None:
                continue
            agg[(sym, side)][i] += p
        agg[(sym, side)][-1] += 1
    return agg, horizons


if __name__ == "__main__":
    print("Plotting cumulative PnL curves...")
    plot_pnl_curves()
    print("Plotting per-product PnL...")
    plot_per_product_pnl()
    print("Plotting all-voucher PnL grid...")
    plot_voucher_pnl()
    for d in (0, 1, 2):
        for sym in ["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT", "VEV_5100",
                    "VEV_5200", "VEV_5300", "VEV_5400", "VEV_4500"]:
            plot_mids_with_trades(d, sym)
    for d in (0, 1, 2):
        for sym in ["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT", "VEV_5100",
                    "VEV_5300", "VEV_5400"]:
            plot_position_curves(d, sym)
    print("Done plotting.")

    # Per-trade attribution
    print("\n=== Per-trade horizon-PnL attribution (v10) ===")
    for d in (0, 1, 2):
        agg, hs = attribute_per_trade(d, "v10")
        print(f"\nDay {d}:")
        items = sorted(agg.items(), key=lambda kv: -abs(kv[1][2]))[:15]
        print(f"  (sym, side)            n     h1       h5      h10     h50    h100")
        for (sym, side), v in items:
            n = v[-1]
            print(f"  {sym:18s} {('B' if side>0 else 'S'):>3s} {n:5d}  {v[0]:7.0f}  {v[1]:7.0f}  {v[2]:7.0f}  {v[3]:7.0f}  {v[4]:7.0f}")
