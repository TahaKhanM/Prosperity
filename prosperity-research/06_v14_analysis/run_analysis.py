"""Round 3 deep statistical analysis for v14 alpha hunt.

Investigates:
1. V5100 day-0 -2649 PnL pathology
2. HYDROGEL drawdown structure on day 2
3. VFE <-> voucher cross-asset signals
4. HYDROGEL microstructure
5. Spectral / cycle analysis
6. Counterparty (verify empty)
7. Trade arrival process

Outputs:
- findings.md
- plots/*.png
"""
from __future__ import annotations

import math
import os
import sys
from collections import defaultdict
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Add bs from round3_options
sys.path.insert(0, "/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/scripts/round3_options")
from bs import bs_call_price, bs_call_vega, bs_call_delta, implied_vol_call

OUT_DIR = "/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_v14_analysis"
PLOT_DIR = os.path.join(OUT_DIR, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)

DATA_DIR = "/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets/round3"

VOUCHER_STRIKES = {
    "VEV_4000": 4000, "VEV_4500": 4500, "VEV_5000": 5000,
    "VEV_5100": 5100, "VEV_5200": 5200, "VEV_5300": 5300,
    "VEV_5400": 5400, "VEV_5500": 5500, "VEV_6000": 6000, "VEV_6500": 6500,
}
VFE = "VELVETFRUIT_EXTRACT"
HYD = "HYDROGEL_PACK"

# Time-to-expiry in calendar days at start of each historical day.
TTE_DAYS = {0: 8, 1: 7, 2: 6}
# Convert to fraction of "year" using 365 (consistent with smile fit script).
def tte_years(day: int) -> float:
    return TTE_DAYS[day] / 365.0


def load_prices(day: int) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"prices_round_3_day_{day}.csv")
    df = pd.read_csv(path, sep=";")
    return df

def load_trades(day: int) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"trades_round_3_day_{day}.csv")
    df = pd.read_csv(path, sep=";")
    return df


# --------------------------------------------------------------------------
# Utility: per-tick wide table with mids
# --------------------------------------------------------------------------
def pivot_mids(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pivot_table(index="timestamp", columns="product",
                              values="mid_price", aggfunc="first")

def pivot_field(prices: pd.DataFrame, field: str) -> pd.DataFrame:
    return prices.pivot_table(index="timestamp", columns="product",
                              values=field, aggfunc="first")


# --------------------------------------------------------------------------
# Section 1: V5100 day-0 pathology
# --------------------------------------------------------------------------
def section_v5100(findings: list[str]) -> None:
    findings.append("\n## 1. V5100 day-0 -2,649 PnL pathology\n")
    rows_per_day = {}
    for d in (0, 1, 2):
        prices = load_prices(d)
        trades = load_trades(d)
        v = prices[prices["product"] == "VEV_5100"].sort_values("timestamp").copy()
        vfe = prices[prices["product"] == VFE].sort_values("timestamp").copy()
        rows_per_day[d] = {"prices": prices, "trades": trades, "v": v, "vfe": vfe}

    # 1a. mid trajectory
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    for d in (0, 1, 2):
        v = rows_per_day[d]["v"]
        axes[d].plot(v["timestamp"], v["mid_price"], lw=0.6)
        axes[d].set_title(f"VEV_5100 mid - day {d} (TTE={TTE_DAYS[d]}d)")
        axes[d].set_ylabel("mid")
        axes[d].grid(alpha=0.3)
    axes[-1].set_xlabel("timestamp")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "01_v5100_mid.png"), dpi=110)
    plt.close()

    # 1b. compute IV per tick using VFE mid as underlying
    iv_table = {}
    for d in (0, 1, 2):
        v = rows_per_day[d]["v"]
        vfe = rows_per_day[d]["vfe"][["timestamp", "mid_price"]].rename(columns={"mid_price": "vfe_mid"})
        v2 = v.merge(vfe, on="timestamp", how="inner")
        t_yr = tte_years(d)
        ivs = []
        for s, k, p in zip(v2["vfe_mid"].values, [5100] * len(v2), v2["mid_price"].values):
            if p < max(s - 5100, 0.0) - 0.5:
                ivs.append(np.nan)
                continue
            iv = implied_vol_call(float(p), float(s), 5100.0, t_yr)
            ivs.append(iv if (iv is not None and not math.isnan(iv)) else np.nan)
        v2["iv"] = ivs
        iv_table[d] = v2

    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    for d in (0, 1, 2):
        v2 = iv_table[d]
        axes[d].plot(v2["timestamp"], v2["iv"], lw=0.6, color="purple")
        axes[d].set_title(f"VEV_5100 IV - day {d} (TTE={TTE_DAYS[d]}d) | mean={v2['iv'].mean():.4f} std={v2['iv'].std():.4f}")
        axes[d].set_ylabel("IV")
        axes[d].grid(alpha=0.3)
    axes[-1].set_xlabel("timestamp")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "02_v5100_iv.png"), dpi=110)
    plt.close()

    # 1c. per-strike IV summary all 3 days
    iv_summary_lines = []
    iv_summary_lines.append("| day | TTE | mean | median | std | min | max | first_500 mean | last_500 mean |")
    iv_summary_lines.append("|-----|-----|------|--------|-----|-----|-----|----------------|---------------|")
    for d in (0, 1, 2):
        v2 = iv_table[d].dropna(subset=["iv"])
        first = v2.iloc[:500]["iv"].mean() if len(v2) > 500 else np.nan
        last = v2.iloc[-500:]["iv"].mean() if len(v2) > 500 else np.nan
        iv_summary_lines.append(
            f"| {d} | {TTE_DAYS[d]}d | {v2['iv'].mean():.5f} | {v2['iv'].median():.5f} | {v2['iv'].std():.5f} | "
            f"{v2['iv'].min():.5f} | {v2['iv'].max():.5f} | {first:.5f} | {last:.5f} |"
        )
    findings.append("### V5100 IV summary\n" + "\n".join(iv_summary_lines) + "\n")

    # 1d. trade clustering for VEV_5100 day 0
    cluster_lines = ["| day | trades | first_ts | last_ts | trades_in_first_10000ts | trades_in_first_50000ts |",
                     "|-----|--------|----------|---------|-------------------------|-------------------------|"]
    for d in (0, 1, 2):
        trades = rows_per_day[d]["trades"]
        v_tr = trades[trades["symbol"] == "VEV_5100"].sort_values("timestamp")
        if len(v_tr):
            f_ts = int(v_tr["timestamp"].min())
            l_ts = int(v_tr["timestamp"].max())
            in10k = (v_tr["timestamp"] < 10000).sum()
            in50k = (v_tr["timestamp"] < 50000).sum()
            cluster_lines.append(f"| {d} | {len(v_tr)} | {f_ts} | {l_ts} | {in10k} | {in50k} |")
    findings.append("### V5100 trade timing\n" + "\n".join(cluster_lines) + "\n")

    # 1e. per-strike day-0 mid mean vs theoretical (using ATM IV from V5300/V5200 as anchor)
    # We'll compute realised mid - "fair smile mid" residual
    # First: collect mid for all vouchers
    findings.append("### Per-strike mid vs naive theo (using ATM IV anchor) - day 0\n")
    # ATM IV: use V5200, which is closest to mean VFE 5246.
    d0 = load_prices(0)
    d0v = d0[d0["product"].isin(VOUCHER_STRIKES.keys())].sort_values(["timestamp", "product"])
    d0vfe = d0[d0["product"] == VFE].sort_values("timestamp")[["timestamp", "mid_price"]].rename(columns={"mid_price": "vfe_mid"})

    # ATM IV per timestamp using V5200
    v52 = d0[d0["product"] == "VEV_5200"][["timestamp", "mid_price"]].merge(d0vfe, on="timestamp", how="inner")
    t_yr = tte_years(0)
    iv_atm = []
    for s, p in zip(v52["vfe_mid"].values, v52["mid_price"].values):
        iv = implied_vol_call(float(p), float(s), 5200.0, t_yr)
        iv_atm.append(iv if (iv is not None and not math.isnan(iv)) else np.nan)
    v52["iv_atm"] = iv_atm
    atm_med = pd.Series(iv_atm).median()
    findings.append(f"- Day 0 ATM IV (V5200) median = **{atm_med:.4f}**\n")

    # Per-strike: mid mean vs BS price using atm_med
    sk_lines = ["| strike | n_ticks | mean_mid | bs_at_atm_iv | residual | first_500_resid | last_500_resid |",
                "|--------|---------|----------|--------------|----------|-----------------|----------------|"]
    for sym, K in VOUCHER_STRIKES.items():
        if K >= 6000:
            continue  # degenerate
        v_d = d0[d0["product"] == sym][["timestamp", "mid_price"]].merge(d0vfe, on="timestamp", how="inner")
        if len(v_d) == 0:
            continue
        bs_prices = [bs_call_price(float(s), float(K), t_yr, atm_med) for s in v_d["vfe_mid"].values]
        v_d["bs"] = bs_prices
        v_d["resid"] = v_d["mid_price"] - v_d["bs"]
        first = v_d.iloc[:500]["resid"].mean() if len(v_d) > 500 else v_d["resid"].mean()
        last = v_d.iloc[-500:]["resid"].mean() if len(v_d) > 500 else v_d["resid"].mean()
        sk_lines.append(f"| {K} | {len(v_d)} | {v_d['mid_price'].mean():.3f} | {v_d['bs'].mean():.3f} | "
                       f"{v_d['resid'].mean():+.3f} | {first:+.3f} | {last:+.3f} |")
    findings.append("\n".join(sk_lines) + "\n")
    findings.append("\n*Interpretation:* `residual = mid - BS(atm_iv)`. Positive residual = market priced HIGHER than naive flat-IV theo (smile premium). Look for V5100 row.\n")

    # 1f. early-tick IV vs full day for V5100
    findings.append("### V5100 IV warmup behavior - day 0\n")
    v51_full = iv_table[0].dropna(subset=["iv"])
    chunks = []
    for chunk in [(0, 5000), (5000, 10000), (10000, 20000), (20000, 50000), (50000, 100000), (100000, 200000)]:
        seg = v51_full[(v51_full["timestamp"] >= chunk[0]) & (v51_full["timestamp"] < chunk[1])]
        if len(seg) == 0:
            continue
        chunks.append(f"| ts [{chunk[0]}, {chunk[1]}) | n={len(seg)} | iv_mean={seg['iv'].mean():.5f} | iv_std={seg['iv'].std():.5f} | mid_mean={seg['mid_price'].mean():.3f} |")
    findings.append("\n".join(chunks) + "\n")

    # 1g. residual behavior over time within day 0 for V5100 specifically
    v51 = d0[d0["product"] == "VEV_5100"][["timestamp", "mid_price"]].merge(d0vfe, on="timestamp", how="inner")
    bs51 = [bs_call_price(float(s), 5100.0, t_yr, atm_med) for s in v51["vfe_mid"].values]
    v51["bs"] = bs51
    v51["resid"] = v51["mid_price"] - v51["bs"]
    # rolling
    fig, ax = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    ax[0].plot(v51["timestamp"], v51["mid_price"], lw=0.5, label="mid")
    ax[0].plot(v51["timestamp"], v51["bs"], lw=0.5, label="BS@ATM_IV")
    ax[0].set_title("VEV_5100 day 0: mid vs BS at ATM_IV(V5200)")
    ax[0].legend()
    ax[0].grid(alpha=0.3)
    ax[1].plot(v51["timestamp"], v51["resid"], lw=0.4, color="darkorange")
    ax[1].axhline(0, color="black", lw=0.6)
    ax[1].set_title("Residual = mid - BS")
    ax[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "03_v5100_residual_day0.png"), dpi=110)
    plt.close()


# --------------------------------------------------------------------------
# Section 2: HYDROGEL drawdown structure
# --------------------------------------------------------------------------
def section_hydrogel_drawdown(findings: list[str]) -> None:
    findings.append("\n## 2. HYDROGEL drawdown structure\n")
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    summary_lines = ["| day | mean | median | std | min | max | %_within_+-5_of_10000 | n_ticks |",
                     "|-----|------|--------|-----|-----|-----|----------------------|---------|"]
    sim_lines = ["| day | sim_pnl | trades_executed | max_long | max_short | drawdown |",
                 "|-----|---------|------------------|----------|-----------|----------|"]
    for d in (0, 1, 2):
        prices = load_prices(d)
        h = prices[prices["product"] == HYD].sort_values("timestamp").copy()
        axes[d].plot(h["timestamp"], h["mid_price"], lw=0.5)
        axes[d].axhline(10000, color="red", lw=0.5, alpha=0.7)
        axes[d].set_title(f"HYDROGEL_PACK mid - day {d}")
        axes[d].grid(alpha=0.3)
        within_5 = ((h["mid_price"] - 10000).abs() <= 5).mean() * 100
        summary_lines.append(
            f"| {d} | {h['mid_price'].mean():.2f} | {h['mid_price'].median():.2f} | "
            f"{h['mid_price'].std():.2f} | {h['mid_price'].min():.2f} | {h['mid_price'].max():.2f} | "
            f"{within_5:.1f}% | {len(h)} |"
        )

        # Simulate H_TAKE=4 anchor=10000 behavior over day
        sim = simulate_hyd_take(h, anchor=10000, take=4, limit=200)
        sim_lines.append(f"| {d} | {sim['pnl']:.0f} | {sim['n']} | {sim['max_long']} | "
                        f"{sim['max_short']} | {sim['drawdown']:.0f} |")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "04_hyd_mid.png"), dpi=110)
    plt.close()
    findings.append("### HYDROGEL mid summary (per day)\n" + "\n".join(summary_lines) + "\n")
    findings.append("### Simulated H_TAKE=4 anchor=10000 sim PnL (no fees, just signed inventory * (mid - exec))\n" + "\n".join(sim_lines) + "\n")

    # Position trajectory + drawdown for day 2
    prices2 = load_prices(2)
    h2 = prices2[prices2["product"] == HYD].sort_values("timestamp").copy()
    sim2 = simulate_hyd_take(h2, anchor=10000, take=4, limit=200, return_path=True)
    fig, ax = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    ax[0].plot(h2["timestamp"], h2["mid_price"], lw=0.5)
    ax[0].axhline(10000, color="red", lw=0.5, alpha=0.6)
    ax[0].set_title("HYDROGEL_PACK day 2 - mid")
    ax[0].grid(alpha=0.3)
    ax[1].plot(sim2["ts_path"], sim2["pos_path"], lw=0.5, color="green")
    ax[1].axhline(0, color="black", lw=0.6)
    ax[1].set_title("Inventory under H_TAKE=4 anchor=10000")
    ax[1].grid(alpha=0.3)
    ax[2].plot(sim2["ts_path"], sim2["pnl_path"], lw=0.6, color="purple")
    ax[2].set_title("Cumulative MTM PnL (anchor=10000)")
    ax[2].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "05_hyd_day2_simulation.png"), dpi=110)
    plt.close()

    # Vol-of-vol: rolling std of mid changes
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    vol_lines = ["| day | rolling_std mean | rolling_std max | quantile80 of |dx| | persistent_burst_pct |",
                  "|-----|------------------|-----------------|--------------------|----------------------|"]
    for d in (0, 1, 2):
        prices = load_prices(d)
        h = prices[prices["product"] == HYD].sort_values("timestamp").copy()
        h["dx"] = h["mid_price"].diff()
        h["abs_dx"] = h["dx"].abs()
        h["roll_std"] = h["dx"].rolling(200).std()
        # persistent burst: |dx| > q90 for 10+ consecutive ticks
        q90 = h["abs_dx"].quantile(0.90)
        h["burst"] = h["abs_dx"] > q90
        # detect runs
        runs = (h["burst"] != h["burst"].shift()).cumsum()
        run_lens = h.groupby(runs)["burst"].agg(lambda s: (s.iloc[0], len(s)))
        long_bursts = sum(1 for v, n in run_lens.values if v and n >= 10)
        burst_pct = (long_bursts * 10) / max(1, len(h)) * 100

        axes[d].plot(h["timestamp"], h["roll_std"], lw=0.5, color="darkred")
        axes[d].set_title(f"HYDROGEL day {d}: rolling-200 std of mid increments")
        axes[d].grid(alpha=0.3)

        vol_lines.append(f"| {d} | {h['roll_std'].mean():.3f} | {h['roll_std'].max():.3f} | "
                         f"{h['abs_dx'].quantile(0.80):.3f} | {burst_pct:.1f}% |")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "06_hyd_volofvol.png"), dpi=110)
    plt.close()
    findings.append("### Vol-of-vol diagnostics\n" + "\n".join(vol_lines) + "\n")

    # Time-of-day effect (drawdown vs % into day)
    findings.append("### Drawdown timing within day\n")
    timing_lines = ["| day | DD_max_ts | total_ticks | %_into_day_at_DD |",
                    "|-----|-----------|-------------|------------------|"]
    for d in (0, 1, 2):
        prices = load_prices(d)
        h = prices[prices["product"] == HYD].sort_values("timestamp").copy()
        sim = simulate_hyd_take(h, anchor=10000, take=4, limit=200, return_path=True)
        pnl_path = pd.Series(sim["pnl_path"], index=sim["ts_path"])
        if len(pnl_path) == 0:
            continue
        running_max = pnl_path.cummax()
        dd = pnl_path - running_max
        idx_dd = dd.idxmin()
        total_ts = pnl_path.index[-1]
        timing_lines.append(f"| {d} | {idx_dd} | {total_ts} | {idx_dd/total_ts*100:.1f}% |")
    findings.append("\n".join(timing_lines) + "\n")


def simulate_hyd_take(h: pd.DataFrame, anchor: float, take: int, limit: int,
                      return_path: bool = False) -> dict:
    """Naive simulation of "take any quote within `take` of anchor" strategy.

    For each tick, if best_ask <= anchor - take/2, BUY at ask; if best_bid >= anchor + take/2, SELL at bid.
    Track cumulative position and MTM = position * (mid - vwap_entry).

    Returns: dict with 'pnl', 'n', 'max_long', 'max_short', 'drawdown', and optionally paths.
    """
    pos = 0
    cash = 0.0
    n = 0
    max_long = 0
    max_short = 0
    pos_path = []
    pnl_path = []
    ts_path = []
    fair = anchor
    threshold_buy = fair - 0.5  # buy if ask is below fair-0.5
    threshold_sell = fair + 0.5  # sell if bid is above fair+0.5
    for _, row in h.iterrows():
        ba = row["best_ask"] if "best_ask" in row else row["ask_price_1"]
        bb = row["best_bid"] if "best_bid" in row else row["bid_price_1"]
        ba_v = row.get("ask_volume_1", 0)
        bb_v = row.get("bid_volume_1", 0)
        mid = row["mid_price"]
        # take any sub-fair ask
        if not pd.isna(ba) and ba <= threshold_buy and pos < limit:
            qty = min(int(ba_v) if not pd.isna(ba_v) else 0, take, limit - pos)
            if qty > 0:
                pos += qty
                cash -= qty * ba
                n += 1
        # take any super-fair bid
        if not pd.isna(bb) and bb >= threshold_sell and pos > -limit:
            qty = min(int(bb_v) if not pd.isna(bb_v) else 0, take, limit + pos)
            if qty > 0:
                pos -= qty
                cash += qty * bb
                n += 1
        max_long = max(max_long, pos)
        max_short = min(max_short, pos)
        if return_path:
            pos_path.append(pos)
            pnl_path.append(cash + pos * mid)
            ts_path.append(row["timestamp"])
    final_pnl = cash + pos * h.iloc[-1]["mid_price"]
    drawdown = 0.0
    if return_path:
        cum = pd.Series(pnl_path)
        rm = cum.cummax()
        drawdown = (cum - rm).min()
    return {
        "pnl": final_pnl, "n": n, "max_long": max_long, "max_short": max_short,
        "drawdown": drawdown, "pos_path": pos_path, "pnl_path": pnl_path, "ts_path": ts_path,
    }


# --------------------------------------------------------------------------
# Section 3: VFE <-> voucher cross-asset signals
# --------------------------------------------------------------------------
def section_cross_asset(findings: list[str]) -> None:
    findings.append("\n## 3. VFE <-> voucher cross-asset signals\n")

    # Use day 0 - all 3 days appended for stability
    all_data = []
    for d in (0, 1, 2):
        df = load_prices(d)
        df["day"] = d
        all_data.append(df)
    combo = pd.concat(all_data, ignore_index=True)

    # Per-day analysis
    lag_summary = ["| day | voucher | lag | corr(dVFE_t, dV_{t+lag}) |",
                   "|-----|---------|-----|--------------------------|"]

    for d in (0, 1, 2):
        df = combo[combo["day"] == d]
        vfe = df[df["product"] == VFE].set_index("timestamp")["mid_price"].sort_index()
        for sym in ("VEV_5300", "VEV_5400", "VEV_5200", "VEV_5100"):
            vd = df[df["product"] == sym].set_index("timestamp")["mid_price"].sort_index()
            joined = pd.concat({"vfe": vfe, "v": vd}, axis=1).dropna()
            if len(joined) < 100:
                continue
            joined["dvfe"] = joined["vfe"].diff()
            joined["dv"] = joined["v"].diff()
            for lag in range(-5, 6):
                if lag == 0:
                    c = joined["dvfe"].corr(joined["dv"])
                elif lag > 0:
                    c = joined["dvfe"].corr(joined["dv"].shift(-lag))
                else:
                    c = joined["dvfe"].corr(joined["dv"].shift(-lag))
                lag_summary.append(f"| {d} | {sym} | {lag:+d} | {c:.4f} |")
    findings.append("### Cross-correlation: dVFE_t vs dV_{t+lag}\n" + "\n".join(lag_summary) + "\n")
    findings.append("*lag>0 means voucher LEADS VFE (informed flow); lag<0 means VFE leads voucher (delta hedge lag).*\n")

    # Order flow imbalance on VFE -> next-tick voucher mid change
    findings.append("### VFE OFI -> next-tick voucher dMid (OLS slope, t-stat)\n")
    ofi_lines = ["| day | voucher | n | beta | t_stat | R^2 |",
                 "|-----|---------|---|------|--------|-----|"]
    for d in (0, 1, 2):
        df = combo[combo["day"] == d]
        vfe = df[df["product"] == VFE].sort_values("timestamp").copy()
        # OFI: contemporaneous quote depth imbalance
        vfe["bid1"] = vfe["bid_price_1"]
        vfe["ask1"] = vfe["ask_price_1"]
        vfe["bv1"] = vfe["bid_volume_1"].fillna(0)
        vfe["av1"] = vfe["ask_volume_1"].fillna(0)
        vfe["ofi"] = (vfe["bv1"] - vfe["av1"]) / (vfe["bv1"] + vfe["av1"]).replace(0, np.nan)
        vfe = vfe[["timestamp", "ofi", "mid_price"]]
        for sym in ("VEV_5300", "VEV_5400", "VEV_5200", "VEV_5100"):
            vd = df[df["product"] == sym].sort_values("timestamp")[["timestamp", "mid_price"]]
            vd = vd.rename(columns={"mid_price": "v_mid"})
            joined = vfe.merge(vd, on="timestamp", how="inner").sort_values("timestamp")
            joined["dv_next"] = joined["v_mid"].shift(-1) - joined["v_mid"]
            joined = joined.dropna(subset=["ofi", "dv_next"])
            if len(joined) < 200:
                continue
            x = joined["ofi"].values
            y = joined["dv_next"].values
            xm = x - x.mean()
            ym = y - y.mean()
            beta = (xm * ym).sum() / (xm * xm).sum() if (xm * xm).sum() > 0 else np.nan
            yhat = beta * xm
            ss_res = ((ym - yhat) ** 2).sum()
            ss_tot = (ym ** 2).sum()
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
            # t-stat
            n = len(joined)
            se = math.sqrt(ss_res / max(1, n - 2)) / math.sqrt((xm * xm).sum())
            t_stat = beta / se if se > 0 else np.nan
            ofi_lines.append(f"| {d} | {sym} | {n} | {beta:.4f} | {t_stat:.2f} | {r2:.5f} |")
    findings.append("\n".join(ofi_lines) + "\n")


# --------------------------------------------------------------------------
# Section 4: HYDROGEL microstructure
# --------------------------------------------------------------------------
def section_hyd_microstructure(findings: list[str]) -> None:
    findings.append("\n## 4. HYDROGEL microstructure\n")

    # Spread distribution
    sp_lines = ["| day | n | spread=1 | spread=2 | spread=3 | spread>=4 | mean | max |",
                "|-----|---|----------|----------|----------|-----------|------|-----|"]
    for d in (0, 1, 2):
        prices = load_prices(d)
        h = prices[prices["product"] == HYD].sort_values("timestamp").copy()
        h["spread"] = h["ask_price_1"] - h["bid_price_1"]
        n = len(h)
        sp_lines.append(
            f"| {d} | {n} | {(h['spread']==1).mean()*100:.1f}% | {(h['spread']==2).mean()*100:.1f}% | "
            f"{(h['spread']==3).mean()*100:.1f}% | {(h['spread']>=4).mean()*100:.1f}% | "
            f"{h['spread'].mean():.2f} | {int(h['spread'].max())} |"
        )
    findings.append("### Spread distribution\n" + "\n".join(sp_lines) + "\n")

    # Wide-spread side asymmetry
    findings.append("### Wide-spread (>=3) side analysis\n")
    side_lines = ["| day | wide_n | bid_step_med | ask_step_med | bid_step>ask_step% | next_dx_when_bid_wide | next_dx_when_ask_wide |",
                  "|-----|--------|--------------|--------------|--------------------|------------------------|-----------------------|"]
    for d in (0, 1, 2):
        prices = load_prices(d)
        h = prices[prices["product"] == HYD].sort_values("timestamp").copy()
        h["spread"] = h["ask_price_1"] - h["bid_price_1"]
        h["mid"] = (h["bid_price_1"] + h["ask_price_1"]) / 2
        h["bid_step"] = h["mid"] - h["bid_price_1"]  # half-spread on bid side
        h["ask_step"] = h["ask_price_1"] - h["mid"]  # half-spread on ask side
        # Asymmetric side: bid_step > ask_step => ask is closer (ask side compressed)
        h["dx_next"] = h["mid"].diff().shift(-1)
        wide = h[h["spread"] >= 3].dropna(subset=["dx_next"])
        if len(wide) == 0:
            continue
        bid_wide = wide[wide["bid_step"] > wide["ask_step"]]
        ask_wide = wide[wide["ask_step"] > wide["bid_step"]]
        side_lines.append(
            f"| {d} | {len(wide)} | {wide['bid_step'].median():.1f} | {wide['ask_step'].median():.1f} | "
            f"{(wide['bid_step']>wide['ask_step']).mean()*100:.1f}% | "
            f"{bid_wide['dx_next'].mean():+.4f} | {ask_wide['dx_next'].mean():+.4f} |"
        )
    findings.append("\n".join(side_lines) + "\n")
    findings.append("*If `bid_wide` next-tick dx is positive, the wider bid (= ask compressed) precedes upward moves. Useful skew signal.*\n")

    # Top-1 vs top-2 imbalance R^2 on next-tick dMid
    findings.append("### Imbalance signal R^2 on next-tick dMid\n")
    imb_lines = ["| day | sig | n | beta | t_stat | R^2 |",
                 "|-----|-----|---|------|--------|-----|"]
    for d in (0, 1, 2):
        prices = load_prices(d)
        h = prices[prices["product"] == HYD].sort_values("timestamp").copy()
        h["mid"] = (h["bid_price_1"] + h["ask_price_1"]) / 2
        h["dx_next"] = h["mid"].diff().shift(-1)
        h["b1"] = h["bid_volume_1"].fillna(0)
        h["a1"] = h["ask_volume_1"].fillna(0)
        h["b2"] = h["bid_volume_2"].fillna(0)
        h["a2"] = h["ask_volume_2"].fillna(0)
        h["imb1"] = (h["b1"] - h["a1"]) / (h["b1"] + h["a1"]).replace(0, np.nan)
        h["imb2"] = ((h["b1"] + h["b2"]) - (h["a1"] + h["a2"])) / ((h["b1"] + h["b2"] + h["a1"] + h["a2"])).replace(0, np.nan)
        # microprice
        h["microprice"] = (h["bid_price_1"] * h["a1"] + h["ask_price_1"] * h["b1"]) / (h["a1"] + h["b1"]).replace(0, np.nan)
        h["mp_dev"] = h["microprice"] - h["mid"]
        # wall-mid: vol >= 15
        bid_wall = h["bid_price_1"].where(h["b1"] >= 15)
        ask_wall = h["ask_price_1"].where(h["a1"] >= 15)
        # use top-2 if top-1 below 15
        h["wall_mid"] = (bid_wall.fillna(h["bid_price_2"]) + ask_wall.fillna(h["ask_price_2"])) / 2
        h["wall_dev"] = h["wall_mid"] - h["mid"]

        for sig_name in ("imb1", "imb2", "mp_dev", "wall_dev"):
            sub = h[[sig_name, "dx_next"]].dropna()
            if len(sub) < 200:
                continue
            x = sub[sig_name].values
            y = sub["dx_next"].values
            xm = x - x.mean()
            ym = y - y.mean()
            beta = (xm * ym).sum() / (xm * xm).sum() if (xm * xm).sum() > 0 else np.nan
            yhat = beta * xm
            ss_res = ((ym - yhat) ** 2).sum()
            ss_tot = (ym ** 2).sum()
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
            n = len(sub)
            se = math.sqrt(ss_res / max(1, n - 2)) / math.sqrt(max(1e-12, (xm * xm).sum()))
            t = beta / se if se > 0 else np.nan
            imb_lines.append(f"| {d} | {sig_name} | {n} | {beta:.4f} | {t:.2f} | {r2:.5f} |")
    findings.append("\n".join(imb_lines) + "\n")


# --------------------------------------------------------------------------
# Section 5: spectral / cycle analysis
# --------------------------------------------------------------------------
def section_spectral(findings: list[str]) -> None:
    findings.append("\n## 5. Spectral / cycle analysis\n")
    fig, axes = plt.subplots(3, 2, figsize=(14, 9))
    spec_lines = ["| product | day | top_period_ticks | spectral_peak_amp | broadband_amp(p<200) |",
                  "|---------|-----|------------------|-------------------|----------------------|"]
    for d in (0, 1, 2):
        prices = load_prices(d)
        h = prices[prices["product"] == HYD].sort_values("timestamp").copy()
        v = prices[prices["product"] == VFE].sort_values("timestamp").copy()
        for col, df_, ax_ in [(0, h, axes[d, 0]), (1, v, axes[d, 1])]:
            x = df_["mid_price"].values - df_["mid_price"].mean()
            n = len(x)
            fft = np.fft.rfft(x)
            mag = np.abs(fft)
            freqs = np.fft.rfftfreq(n, d=1.0)
            # period = 1/freq in tick units
            with np.errstate(divide="ignore"):
                periods = np.where(freqs > 0, 1.0 / freqs, np.nan)
            # find dominant peak in 200-10000 tick window
            mask = (periods >= 200) & (periods <= 10000)
            if mask.any():
                idx = np.argmax(mag * mask)
                peak_period = periods[idx]
                peak_amp = mag[idx]
            else:
                peak_period = np.nan
                peak_amp = np.nan
            broad = mag[(periods < 200)].mean() if (periods < 200).any() else np.nan
            ax_.plot(periods[mask], mag[mask], lw=0.6)
            ax_.set_xscale("log")
            prod_name = "HYD" if col == 0 else "VFE"
            ax_.set_title(f"{prod_name} day {d}: peak={peak_period:.0f}t amp={peak_amp:.1f}")
            ax_.set_xlabel("period (ticks)")
            ax_.set_ylabel("|FFT|")
            ax_.grid(alpha=0.3)
            spec_lines.append(f"| {prod_name} | {d} | {peak_period:.0f} | {peak_amp:.1f} | {broad:.2f} |")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "07_spectral.png"), dpi=110)
    plt.close()
    findings.append("\n".join(spec_lines) + "\n")


# --------------------------------------------------------------------------
# Section 6: counterparty empty check
# --------------------------------------------------------------------------
def section_counterparty(findings: list[str]) -> None:
    findings.append("\n## 6. Counterparty fields verification\n")
    cp_lines = ["| day | n_trades | %_buyer_empty | %_seller_empty | unique_buyers | unique_sellers |",
                "|-----|----------|---------------|----------------|---------------|----------------|"]
    for d in (0, 1, 2):
        tr = load_trades(d)
        n = len(tr)
        buyer_empty = tr["buyer"].isna().mean() * 100
        seller_empty = tr["seller"].isna().mean() * 100
        ub = tr["buyer"].dropna().unique()
        us = tr["seller"].dropna().unique()
        cp_lines.append(f"| {d} | {n} | {buyer_empty:.1f}% | {seller_empty:.1f}% | "
                       f"{len(ub)} ({list(ub)[:3]}) | {len(us)} ({list(us)[:3]}) |")
    findings.append("\n".join(cp_lines) + "\n")


# --------------------------------------------------------------------------
# Section 7: trade arrival
# --------------------------------------------------------------------------
def section_trade_arrival(findings: list[str]) -> None:
    findings.append("\n## 7. Trade arrival process\n")
    arr_lines = ["| day | product | n | mean_iat | median_iat | iat_q90 | mean_size | size_mode | size>=20 % |",
                 "|-----|---------|---|----------|------------|---------|-----------|-----------|------------|"]
    for d in (0, 1, 2):
        tr = load_trades(d)
        for prod in (HYD, VFE, "VEV_5200", "VEV_5300", "VEV_5400"):
            sub = tr[tr["symbol"] == prod].sort_values("timestamp")
            if len(sub) < 5:
                continue
            iat = sub["timestamp"].diff().dropna()
            arr_lines.append(
                f"| {d} | {prod} | {len(sub)} | {iat.mean():.0f} | {iat.median():.0f} | "
                f"{iat.quantile(0.9):.0f} | {sub['quantity'].mean():.2f} | "
                f"{int(sub['quantity'].mode().iloc[0]) if len(sub['quantity'].mode()) else -1} | "
                f"{(sub['quantity']>=20).mean()*100:.1f}% |"
            )
    findings.append("\n".join(arr_lines) + "\n")

    # Size histograms
    fig, axes = plt.subplots(2, 3, figsize=(14, 7))
    for i, prod in enumerate([HYD, VFE, "VEV_5300"]):
        for d in (0, 1, 2):
            tr = load_trades(d)
            sub = tr[tr["symbol"] == prod]["quantity"]
            axes[d % 2, i].hist(sub, bins=30, alpha=0.4, label=f"d{d}")
        axes[0, i].set_title(f"{prod} trade size")
        axes[0, i].legend()
        axes[0, i].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "08_trade_size_hist.png"), dpi=110)
    plt.close()


# --------------------------------------------------------------------------
# Section 8: smile drift (TTE-indexed)
# --------------------------------------------------------------------------
def section_smile(findings: list[str]) -> None:
    findings.append("\n## 8. Smile drift across TTE 8d->6d\n")
    smile_lines = ["| day | TTE | strike | iv_mean | iv_med | iv_std | n |",
                   "|-----|-----|--------|---------|--------|--------|---|"]
    smile_table: Dict[int, Dict[int, float]] = {}
    for d in (0, 1, 2):
        prices = load_prices(d)
        vfe = prices[prices["product"] == VFE].set_index("timestamp")["mid_price"]
        smile_table[d] = {}
        t_yr = tte_years(d)
        for sym, K in VOUCHER_STRIKES.items():
            if K >= 6000:
                continue
            v = prices[prices["product"] == sym].set_index("timestamp")["mid_price"]
            joined = pd.concat({"vfe": vfe, "v": v}, axis=1).dropna()
            ivs = []
            for s, p in zip(joined["vfe"].values, joined["v"].values):
                iv = implied_vol_call(float(p), float(s), float(K), t_yr)
                if iv is not None and not math.isnan(iv):
                    ivs.append(iv)
            ivs = pd.Series(ivs)
            smile_table[d][K] = ivs.median()
            smile_lines.append(f"| {d} | {TTE_DAYS[d]}d | {K} | {ivs.mean():.5f} | {ivs.median():.5f} | "
                              f"{ivs.std():.5f} | {len(ivs)} |")
    findings.append("\n".join(smile_lines) + "\n")

    # Plot smile per day
    fig, ax = plt.subplots(figsize=(10, 5))
    for d in (0, 1, 2):
        ks = sorted(smile_table[d].keys())
        ivs = [smile_table[d][k] for k in ks]
        ax.plot(ks, ivs, marker="o", label=f"day {d} (TTE={TTE_DAYS[d]}d)")
    ax.set_xlabel("strike")
    ax.set_ylabel("median IV")
    ax.set_title("Smile drift (median IV per strike across TTEs)")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "09_smile_drift.png"), dpi=110)
    plt.close()


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    findings: list[str] = []
    findings.append("# Round 3 v14 deep statistical analysis\n")
    findings.append("Run date: 2026-04-25. Data: prices+trades day_{0,1,2}.csv (semicolon-sep).\n")

    print("[1/8] V5100 day-0 pathology...")
    section_v5100(findings)
    print("[2/8] HYDROGEL drawdown...")
    section_hydrogel_drawdown(findings)
    print("[3/8] Cross-asset signals...")
    section_cross_asset(findings)
    print("[4/8] HYDROGEL microstructure...")
    section_hyd_microstructure(findings)
    print("[5/8] Spectral...")
    section_spectral(findings)
    print("[6/8] Counterparty check...")
    section_counterparty(findings)
    print("[7/8] Trade arrival...")
    section_trade_arrival(findings)
    print("[8/8] Smile drift...")
    section_smile(findings)

    out = "\n".join(findings)
    out_path = os.path.join(OUT_DIR, "findings.md")
    with open(out_path, "w") as f:
        f.write(out)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
