#!/usr/bin/env python3
"""
IMC Prosperity 4 — Visual Market Analysis Tool
================================================
Produces decision-grade plots for every product.
Each chart answers: "which strategy, and how to parameterise it?"

Run:  python analysis.py          (from the data directory)
Also: analysis.ipynb              (same code, cell-by-cell)
"""

import glob, os, warnings, itertools, math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.ticker as mticker
from scipy import stats as sp_stats

warnings.filterwarnings("ignore")
plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "figure.facecolor": "white",
    "axes.facecolor": "#f8f8f8", "axes.grid": True, "grid.alpha": 0.3,
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "legend.fontsize": 8, "figure.titlesize": 12,
})
PLOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
os.makedirs(PLOT_DIR, exist_ok=True)
DAY_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
              "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

def savefig(fig, name):
    fig.savefig(os.path.join(PLOT_DIR, f"{name}.png"), bbox_inches="tight")
    plt.close(fig)

# ═══════════════════════════════════════════════════════════════════════
# SECTION 1 — DATA LOADING
# ═══════════════════════════════════════════════════════════════════════
def load_data():
    """Auto-detect and load all price and trade CSVs."""
    base = os.path.dirname(os.path.abspath(__file__))
    price_files = sorted(glob.glob(os.path.join(base, "prices_round_*_day_*.csv")))
    trade_files = sorted(glob.glob(os.path.join(base, "trades_round_*_day_*.csv")))

    prices = pd.concat([pd.read_csv(f, sep=";") for f in price_files], ignore_index=True)
    trades = pd.concat([pd.read_csv(f, sep=";") for f in trade_files], ignore_index=True)

    # Ensure numeric
    num_cols = [c for c in prices.columns if c not in ("product",)]
    for c in num_cols:
        prices[c] = pd.to_numeric(prices[c], errors="coerce")

    for c in ["price", "quantity", "timestamp"]:
        if c in trades.columns:
            trades[c] = pd.to_numeric(trades[c], errors="coerce")

    products = sorted(prices["product"].unique())
    product_dfs = {p: prices[prices["product"] == p].copy().reset_index(drop=True)
                   for p in products}

    # Rename 'symbol' → uniform key for trades
    if "symbol" in trades.columns:
        trades = trades.rename(columns={"symbol": "product"})

    trade_dfs = {p: trades[trades["product"] == p].copy().reset_index(drop=True)
                 for p in products if p in trades["product"].unique()}

    print("=" * 72)
    print("SECTION 1 — DATA LOADING SUMMARY")
    print("=" * 72)
    print(f"Price files loaded : {len(price_files)}")
    print(f"Trade files loaded : {len(trade_files)}")
    print(f"Total price rows   : {len(prices):,}")
    print(f"Total trade rows   : {len(trades):,}")
    print(f"Products           : {products}")
    print(f"Days               : {sorted(prices['day'].unique())}")
    print()
    for p in products:
        df = product_dfs[p]
        print(f"  {p:15s}  rows={len(df):>6,}  "
              f"mid=[{df['mid_price'].min():.1f}, {df['mid_price'].max():.1f}]  "
              f"days={sorted(df['day'].unique())}")
    print()

    return products, product_dfs, trade_dfs


# ═══════════════════════════════════════════════════════════════════════
# HELPER — compute all derived columns on a per-product df
# ═══════════════════════════════════════════════════════════════════════
def compute_features(df):
    """Add all helper columns to a single-product dataframe."""
    d = df.copy()
    # Simple mid
    d["simple_mid"] = (d["bid_price_1"] + d["ask_price_1"]) / 2

    # Microprice
    bv1 = d["bid_volume_1"].fillna(0)
    av1 = d["ask_volume_1"].fillna(0)
    denom = bv1 + av1
    d["microprice"] = np.where(denom > 0,
        (d["bid_price_1"] * av1 + d["ask_price_1"] * bv1) / denom,
        d["simple_mid"])

    # Wall mid
    bid_prices = d[["bid_price_1", "bid_price_2", "bid_price_3"]].values
    bid_vols   = d[["bid_volume_1", "bid_volume_2", "bid_volume_3"]].fillna(0).values
    ask_prices = d[["ask_price_1", "ask_price_2", "ask_price_3"]].values
    ask_vols   = d[["ask_volume_1", "ask_volume_2", "ask_volume_3"]].fillna(0).values

    bid_wall = np.array([bp[np.nanargmax(bv)] if np.nanmax(bv) > 0 else bp[0]
                         for bp, bv in zip(bid_prices, bid_vols)])
    ask_wall = np.array([ap[np.nanargmax(av)] if np.nanmax(av) > 0 else ap[0]
                         for ap, av in zip(ask_prices, ask_vols)])
    d["bid_wall_price"] = bid_wall
    d["ask_wall_price"] = ask_wall
    d["wall_mid"] = (bid_wall + ask_wall) / 2

    # Spread
    d["spread"] = d["ask_price_1"] - d["bid_price_1"]

    # Book imbalance
    total_bid = d[["bid_volume_1", "bid_volume_2", "bid_volume_3"]].fillna(0).sum(axis=1)
    total_ask = d[["ask_volume_1", "ask_volume_2", "ask_volume_3"]].fillna(0).sum(axis=1)
    d["imbalance"] = (total_bid - total_ask) / (total_bid + total_ask).replace(0, np.nan)

    # Returns & rolling vol
    d["ret"] = d["mid_price"].diff()
    d["rolling_vol"] = d["ret"].rolling(10).std()
    d["rolling_vol_20"] = d["ret"].rolling(20).std()

    # Z-score
    rm20 = d["mid_price"].rolling(20).mean()
    rs20 = d["mid_price"].rolling(20).std()
    d["z20"] = (d["mid_price"] - rm20) / rs20.replace(0, np.nan)

    # Spike flag
    d["spike"] = d["ret"].abs() > 3 * d["rolling_vol"]

    # Signals for Section 6
    d["ret1"] = d["ret"]
    d["micro_delta"] = d["microprice"] - d["simple_mid"]
    d["wall_delta"] = d["wall_mid"] - d["simple_mid"]
    d["spread_chg"] = d["spread"].diff()
    d["next_ret"] = d["mid_price"].diff().shift(-1)

    return d


# ═══════════════════════════════════════════════════════════════════════
# SECTION 2 — IS THIS PRODUCT STABLE, DRIFTING OR VOLATILE?
# ═══════════════════════════════════════════════════════════════════════
def classify_product(cv):
    if cv < 0.001:
        return "STABLE"
    elif cv < 0.01:
        return "DRIFTING"
    else:
        return "VOLATILE"

def section2(products, feat_dfs):
    print("=" * 72)
    print("SECTION 2 — IS THIS PRODUCT STABLE, DRIFTING OR VOLATILE?")
    print("=" * 72)

    n = len(products)

    # --- Plot 2A ---
    fig, axes = plt.subplots(1, n, figsize=(12 * n / 2, 6), squeeze=False)
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        df = feat_dfs[p]
        days = sorted(df["day"].unique())
        for di, day in enumerate(days):
            dd = df[df["day"] == day]
            ax.plot(dd["timestamp"], dd["mid_price"],
                    color=DAY_COLORS[di % len(DAY_COLORS)],
                    alpha=0.7, linewidth=0.6, label=f"Day {day}")
        mean_p = df["mid_price"].mean()
        ax.axhline(mean_p, color="black", linestyle="--", linewidth=1.2,
                   label=f"Mean={mean_p:.1f}")
        ax.set_title(f"{p} – Does price revert to a fixed anchor? (→ stable MM)\n"
                     f"or drift freely? (→ dynamic FV) or spike? (→ reversion)",
                     fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Mid Price")
        ax.legend(fontsize=7)
    fig.suptitle("Plot 2A — Price History: Stability Classification", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "2A_price_history")

    # --- Plot 2B ---
    fig, axes = plt.subplots(1, n, figsize=(12 * n / 2, 5), squeeze=False)
    verdicts = {}
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        df = feat_dfs[p]
        mid = df["mid_price"].dropna()
        mean_p = mid.mean(); std_p = mid.std(); cv = std_p / mean_p
        verdict = classify_product(cv)
        verdicts[p] = verdict
        ax.hist(mid, bins=80, color="#5599dd", edgecolor="white", alpha=0.8)
        ax.axvline(mean_p, color="red", linestyle="--", linewidth=1.5,
                   label=f"Mean={mean_p:.1f}")
        ax.set_title(f"{p} – Price distribution (std={std_p:.2f}) → {verdict}",
                     fontsize=9)
        ax.set_xlabel("Mid Price"); ax.set_ylabel("Frequency")
        ax.legend()
        ax.annotate(f"CV = {cv:.6f}\n→ {verdict}",
                    xy=(0.72, 0.85), xycoords="axes fraction",
                    fontsize=8, bbox=dict(boxstyle="round,pad=0.3",
                    fc="lightyellow", ec="orange"))
    fig.suptitle("Plot 2B — Price Distribution: Range Classification", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "2B_price_distribution")

    # --- Plot 2C ---
    fig, axes = plt.subplots(1, n, figsize=(12 * n / 2, 5), squeeze=False)
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        df = feat_dfs[p]
        days = sorted(df["day"].unique())
        for di, day in enumerate(days):
            dd = df[df["day"] == day]
            ax.plot(dd["timestamp"], dd["rolling_vol_20"],
                    color=DAY_COLORS[di % len(DAY_COLORS)],
                    alpha=0.7, linewidth=0.6, label=f"Day {day}")
        mean_vol = df["rolling_vol_20"].mean()
        ax.axhline(mean_vol, color="red", linestyle="--", linewidth=1.2,
                   label=f"Mean vol={mean_vol:.3f}")
        ax.set_title(f"{p} – Is volatility constant or regime-switching?\n"
                     f"(spikes above line = dangerous periods for market making)",
                     fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Rolling 20-tick Std of Returns")
        ax.legend(fontsize=7)
    fig.suptitle("Plot 2C — Rolling Volatility", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "2C_rolling_volatility")

    # --- Print summary ---
    strat_map = {"STABLE": "Fixed Fair Value Market Making",
                 "DRIFTING": "Dynamic / Rolling Fair Value MM",
                 "VOLATILE": "Spike Reversion + Wide-edge MM"}
    for p in products:
        df = feat_dfs[p]
        mid = df["mid_price"]
        m, s = mid.mean(), mid.std()
        cv = s / m
        v = classify_product(cv)
        print(f"  {p:15s}  mean={m:.2f}  std={s:.3f}  CV={cv:.6f}  "
              f"→ {v}  →  {strat_map[v]}")
    print()
    return verdicts


# ═══════════════════════════════════════════════════════════════════════
# SECTION 3 — WHAT IS THE FAIR VALUE?
# ═══════════════════════════════════════════════════════════════════════
def section3(products, feat_dfs):
    print("=" * 72)
    print("SECTION 3 — WHAT IS THE FAIR VALUE?")
    print("=" * 72)

    fv_results = {}

    for p in products:
        df = feat_dfs[p]

        # --- Plot 3A ---
        fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
        ax1, ax2, ax3 = axes

        ax1.plot(df["timestamp"], df["simple_mid"], alpha=0.7, linewidth=0.5,
                 label="Simple Mid", color="#1f77b4")
        ax1.plot(df["timestamp"], df["microprice"], alpha=0.7, linewidth=0.5,
                 label="Microprice", color="#ff7f0e")
        ax1.plot(df["timestamp"], df["wall_mid"], alpha=0.7, linewidth=0.5,
                 label="Wall Mid", color="#2ca02c")
        ax1.fill_between(df["timestamp"], df["simple_mid"], df["wall_mid"],
                         alpha=0.15, color="green", label="Simple↔Wall gap")
        ax1.set_ylabel("Price"); ax1.legend(fontsize=7)
        ax1.set_title(f"{p} – Which fair value estimate is most stable?\n"
                      f"(less noisy = better anchor for your strategy)", fontsize=9)

        ax2.plot(df["timestamp"], df["microprice"] - df["simple_mid"],
                 alpha=0.7, linewidth=0.5, color="#ff7f0e")
        ax2.axhline(0, color="black", linewidth=0.5)
        ax2.set_ylabel("Microprice − Simple Mid")
        ax2.set_title("Panel 2: Microprice deviation from simple mid", fontsize=8)

        ax3.plot(df["timestamp"], df["wall_mid"] - df["simple_mid"],
                 alpha=0.7, linewidth=0.5, color="#2ca02c")
        ax3.axhline(0, color="black", linewidth=0.5)
        ax3.set_ylabel("Wall Mid − Simple Mid")
        ax3.set_xlabel("Timestamp")
        ax3.set_title("Panel 3: Wall mid deviation from simple mid", fontsize=8)

        fig.suptitle(f"Plot 3A — {p}: Fair Value Comparison", fontsize=12, y=1.01)
        fig.tight_layout()
        savefig(fig, f"3A_fair_value_comparison_{p}")

        # --- Plot 3B ---
        fig, ax = plt.subplots(figsize=(14, 6))
        # Sample for performance
        step = max(1, len(df) // 4000)
        ds = df.iloc[::step]

        vol_cols_bid = ["bid_volume_1", "bid_volume_2", "bid_volume_3"]
        vol_cols_ask = ["ask_volume_1", "ask_volume_2", "ask_volume_3"]
        price_cols_bid = ["bid_price_1", "bid_price_2", "bid_price_3"]
        price_cols_ask = ["ask_price_1", "ask_price_2", "ask_price_3"]

        all_bid_vols = ds[vol_cols_bid].fillna(0).values.flatten()
        all_ask_vols = ds[vol_cols_ask].fillna(0).values.flatten()
        all_vols = np.concatenate([all_bid_vols[all_bid_vols > 0],
                                   all_ask_vols[all_ask_vols > 0]])
        vol_75 = np.percentile(all_vols, 75) if len(all_vols) > 0 else 1

        for i in range(3):
            bv = ds[vol_cols_bid[i]].fillna(0)
            bp = ds[price_cols_bid[i]]
            mask = bv > 0
            sizes = np.clip(bv[mask] / vol_75 * 15, 2, 60)
            ax.scatter(ds["timestamp"][mask], bp[mask], s=sizes,
                       alpha=0.15, color="blue", edgecolors="none")
            # Wall quotes
            wall_mask = mask & (bv > vol_75)
            if wall_mask.any():
                ax.scatter(ds["timestamp"][wall_mask], bp[wall_mask],
                           s=np.clip(bv[wall_mask] / vol_75 * 30, 20, 120),
                           alpha=0.5, color="blue", edgecolors="darkblue",
                           linewidth=0.5, label="Bid wall" if i == 0 else "")

            av = ds[vol_cols_ask[i]].fillna(0)
            ap = ds[price_cols_ask[i]]
            mask_a = av > 0
            sizes_a = np.clip(av[mask_a] / vol_75 * 15, 2, 60)
            ax.scatter(ds["timestamp"][mask_a], ap[mask_a], s=sizes_a,
                       alpha=0.15, color="red", edgecolors="none")
            wall_mask_a = mask_a & (av > vol_75)
            if wall_mask_a.any():
                ax.scatter(ds["timestamp"][wall_mask_a], ap[wall_mask_a],
                           s=np.clip(av[wall_mask_a] / vol_75 * 30, 20, 120),
                           alpha=0.5, color="red", edgecolors="darkred",
                           linewidth=0.5, label="Ask wall" if i == 0 else "")

        ax.plot(ds["timestamp"], ds["wall_mid"], color="black", linewidth=1,
                alpha=0.8, label="Wall Mid")
        ax.set_title(f"{p} – Order book structure: where are the walls?\n"
                     f"(large dots = likely bot market makers who know fair value)",
                     fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Price")
        ax.legend(fontsize=7)
        fig.tight_layout()
        savefig(fig, f"3B_wall_quotes_{p}")

        # Compute FV stds
        std_simple = df["simple_mid"].std()
        std_micro = df["microprice"].std()
        std_wall = df["wall_mid"].std()
        fv_results[p] = {"simple_mid_std": std_simple,
                         "microprice_std": std_micro,
                         "wall_mid_std": std_wall}

    # --- Plot 3C ---
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(products))
    w = 0.25
    for i, method in enumerate(["simple_mid_std", "microprice_std", "wall_mid_std"]):
        vals = [fv_results[p][method] for p in products]
        label = method.replace("_std", "").replace("_", " ").title()
        ax.bar(x + i * w, vals, w, label=label,
               color=["#1f77b4", "#ff7f0e", "#2ca02c"][i], alpha=0.8)
    ax.set_xticks(x + w); ax.set_xticklabels(products)
    ax.set_ylabel("Std of Fair Value Estimate")
    ax.set_title("Plot 3C — Which fair value has lowest noise?\n"
                 "(lowest bar = use this as your fair value estimate)", fontsize=10)
    ax.legend()
    fig.tight_layout()
    savefig(fig, "3C_fair_value_stability_ranking")

    for p in products:
        r = fv_results[p]
        best = min(r, key=r.get).replace("_std", "")
        print(f"  {p:15s}  simple_mid_std={r['simple_mid_std']:.4f}  "
              f"microprice_std={r['microprice_std']:.4f}  "
              f"wall_mid_std={r['wall_mid_std']:.4f}  →  USE: {best}")
    print()
    return fv_results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 4 — IS THERE SPREAD TO CAPTURE?
# ═══════════════════════════════════════════════════════════════════════
def section4(products, feat_dfs):
    print("=" * 72)
    print("SECTION 4 — IS THERE SPREAD TO CAPTURE?")
    print("=" * 72)
    n = len(products)
    spread_results = {}

    # --- Plot 4A ---
    fig, axes = plt.subplots(1, n, figsize=(12 * n / 2, 5), squeeze=False)
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        df = feat_dfs[p]
        days = sorted(df["day"].unique())
        for di, day in enumerate(days):
            dd = df[df["day"] == day]
            ax.plot(dd["timestamp"], dd["spread"],
                    color=DAY_COLORS[di % len(DAY_COLORS)],
                    alpha=0.6, linewidth=0.5, label=f"Day {day}")
        sp = df["spread"].dropna()
        m_sp, s_sp = sp.mean(), sp.std()
        ax.axhline(m_sp, color="black", linestyle="--", linewidth=1, label=f"Mean={m_sp:.2f}")
        ax.axhline(m_sp - s_sp, color="orange", linestyle=":", linewidth=0.8, label=f"−1σ={m_sp - s_sp:.2f}")
        ax.axhline(m_sp + s_sp, color="orange", linestyle=":", linewidth=0.8, label=f"+1σ={m_sp + s_sp:.2f}")
        ax.fill_between(df["timestamp"], 0, m_sp, alpha=0.08, color="red")
        ax.set_title(f"{p} – Spread over time: is market making profitable?\n"
                     f"(spread must consistently exceed your take/passive edges)",
                     fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Bid-Ask Spread")
        ax.legend(fontsize=6)
    fig.suptitle("Plot 4A — Spread Over Time", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "4A_spread_over_time")

    # --- Plot 4B ---
    fig, axes = plt.subplots(1, n, figsize=(12 * n / 2, 5), squeeze=False)
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        df = feat_dfs[p]
        sp = df["spread"].dropna()
        ax.hist(sp, bins=60, color="#5599dd", edgecolor="white", alpha=0.8)
        p25, p50, p75 = sp.quantile(0.25), sp.quantile(0.5), sp.quantile(0.75)
        for pval, lab, col in [(p25, "25th", "green"), (p50, "50th", "orange"), (p75, "75th", "red")]:
            ax.axvline(pval, color=col, linestyle="--", linewidth=1.2, label=f"{lab}={pval:.1f}")
        te = p25 / 4; pe = p50 / 3
        ax.annotate(f"take_edge candidate = {te:.2f}\npassive_edge candidate = {pe:.2f}",
                    xy=(0.55, 0.80), xycoords="axes fraction", fontsize=7,
                    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="orange"))
        ax.set_title(f"{p} – Spread distribution: edge parameter guide\n"
                     f"(take_edge + passive_edge < typical spread)", fontsize=9)
        ax.set_xlabel("Spread"); ax.set_ylabel("Frequency")
        ax.legend(fontsize=7)
        spread_results[p] = {"mean": sp.mean(), "std": sp.std(),
                             "p25": p25, "p50": p50, "p75": p75,
                             "take_edge": te, "passive_edge": pe}
    fig.suptitle("Plot 4B — Spread Distribution", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "4B_spread_distribution")

    # --- Plot 4C ---
    fig, axes = plt.subplots(1, n, figsize=(12 * n / 2, 5), squeeze=False)
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        sr = spread_results[p]
        mean_sp = sr["mean"]
        te_range = np.linspace(0.5, max(sr["p75"], mean_sp * 1.5), 200)
        profit = mean_sp - 2 * te_range
        ax.plot(te_range, profit, color="#1f77b4", linewidth=2)
        ax.axhline(0, color="red", linestyle="--", linewidth=1)
        ax.axvline(sr["take_edge"], color="green", linestyle="--", linewidth=1.2,
                   label=f"Suggested take_edge={sr['take_edge']:.2f}")
        ax.fill_between(te_range, profit, 0, where=(profit > 0),
                        alpha=0.1, color="green")
        ax.fill_between(te_range, profit, 0, where=(profit <= 0),
                        alpha=0.1, color="red")
        ax.set_title(f"{p} – Round trip profit vs take edge\n"
                     f"(where line crosses zero = edge too large to trade)", fontsize=9)
        ax.set_xlabel("Take Edge"); ax.set_ylabel("Theoretical Profit per Round Trip")
        ax.legend(fontsize=7)
    fig.suptitle("Plot 4C — Theoretical PnL per Round Trip", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "4C_theoretical_pnl")

    for p in products:
        sr = spread_results[p]
        rt_profit = sr["mean"] - 2 * sr["take_edge"]
        print(f"  {p:15s}  mean_spread={sr['mean']:.2f}  "
              f"p25/p50/p75={sr['p25']:.1f}/{sr['p50']:.1f}/{sr['p75']:.1f}  "
              f"take_edge={sr['take_edge']:.2f}  passive_edge={sr['passive_edge']:.2f}  "
              f"RT_profit={rt_profit:.2f}")
    print()
    return spread_results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 5 — DOES PRICE MEAN REVERT OR TREND?
# ═══════════════════════════════════════════════════════════════════════
def section5(products, feat_dfs):
    print("=" * 72)
    print("SECTION 5 — DOES PRICE MEAN REVERT OR TREND?")
    print("=" * 72)
    n = len(products)
    acf_results = {}

    # --- Plot 5A ---
    fig, axes = plt.subplots(1, n, figsize=(12 * n / 2, 5), squeeze=False)
    lags = [1, 2, 3, 5, 10]
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        df = feat_dfs[p]
        rets = df["ret"].dropna()
        acfs = [rets.autocorr(lag=l) for l in lags]
        colors = ["#d62728" if a < 0 else "#1f77b4" for a in acfs]
        ax.bar(range(len(lags)), acfs, color=colors, edgecolor="white", alpha=0.8)
        ax.set_xticks(range(len(lags))); ax.set_xticklabels([str(l) for l in lags])
        ax.axhline(0, color="black", linewidth=0.5)
        ax.axhline(0.05, color="gray", linestyle=":", linewidth=0.8, label="±0.05 sig")
        ax.axhline(-0.05, color="gray", linestyle=":", linewidth=0.8)
        ax.set_title(f"{p} – Return autocorrelation:\n"
                     f"RED = mean reverting (MM aggressively) | "
                     f"BLUE = trending (directional bias)", fontsize=8)
        ax.set_xlabel("Lag"); ax.set_ylabel("Autocorrelation")
        ax.legend(fontsize=7)
        acf_results[p] = {"lag1": acfs[0], "acfs": dict(zip(lags, acfs))}
    fig.suptitle("Plot 5A — Autocorrelation of Returns", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "5A_autocorrelation")

    # --- Plot 5B ---
    for p in products:
        df = feat_dfs[p]
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        rm = df["mid_price"].rolling(20).mean()
        rs = df["mid_price"].rolling(20).std()

        ax1.plot(df["timestamp"], df["mid_price"], alpha=0.7, linewidth=0.5,
                 color="#1f77b4", label="Mid Price")
        ax1.plot(df["timestamp"], rm, color="black", linewidth=1, label="Rolling 20 Mean")
        above = df["mid_price"] > rm + rs
        below = df["mid_price"] < rm - rs
        ax1.fill_between(df["timestamp"], df["mid_price"], rm,
                         where=above, alpha=0.3, color="red", label="Sell zone (>1σ)")
        ax1.fill_between(df["timestamp"], df["mid_price"], rm,
                         where=below, alpha=0.3, color="green", label="Buy zone (<−1σ)")
        ax1.set_ylabel("Mid Price"); ax1.legend(fontsize=7)

        ax2.plot(df["timestamp"], df["z20"], alpha=0.7, linewidth=0.5, color="#ff7f0e")
        for lv, ls in [(1, "--"), (2, ":"), (-1, "--"), (-2, ":")]:
            ax2.axhline(lv, color="gray", linestyle=ls, linewidth=0.7,
                        label=f"±{abs(lv)}σ" if lv > 0 else "")
        ax2.axhline(0, color="black", linewidth=0.5)
        ax2.set_ylabel("Z-Score (20-tick)"); ax2.set_xlabel("Timestamp")
        ax2.legend(fontsize=7)

        fig.suptitle(f"Plot 5B — {p} – Mean reversion test:\n"
                     f"shaded = sell (red) / buy (green) | "
                     f"tight z-score = strong mean reversion", fontsize=10, y=1.01)
        fig.tight_layout()
        savefig(fig, f"5B_zscore_{p}")

    # --- Plot 5C ---
    fig, axes = plt.subplots(1, n, figsize=(12 * n / 2, 5), squeeze=False)
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        df = feat_dfs[p]
        rets = df["ret"].dropna()
        ax.hist(rets, bins=100, density=True, color="#5599dd",
                edgecolor="white", alpha=0.7, label="Actual returns")
        # Overlay normal
        x = np.linspace(rets.min(), rets.max(), 300)
        ax.plot(x, sp_stats.norm.pdf(x, rets.mean(), rets.std()),
                color="red", linewidth=1.5, label="Normal fit")
        kurt = rets.kurtosis()
        ax.annotate(f"Kurtosis = {kurt:.2f}\n{'Fat tails!' if kurt > 3 else 'Near-normal'}",
                    xy=(0.65, 0.85), xycoords="axes fraction", fontsize=7,
                    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="orange"))
        ax.set_title(f"{p} – Return distribution:\n"
                     f"fat tails = spike risk | normal tails = safe to MM tightly",
                     fontsize=8)
        ax.set_xlabel("Return"); ax.set_ylabel("Density")
        ax.legend(fontsize=7)
    fig.suptitle("Plot 5C — Return Distribution", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "5C_return_distribution")

    for p in products:
        lag1 = acf_results[p]["lag1"]
        verdict = "MEAN REVERTING" if lag1 < -0.05 else ("TRENDING" if lag1 > 0.05 else "NEUTRAL")
        print(f"  {p:15s}  lag-1 autocorr = {lag1:.4f}  →  {verdict}")
    print()
    return acf_results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 6 — WHICH SIGNALS PREDICT PRICE DIRECTION?
# ═══════════════════════════════════════════════════════════════════════
def section6(products, feat_dfs):
    print("=" * 72)
    print("SECTION 6 — WHICH SIGNALS PREDICT PRICE DIRECTION?")
    print("=" * 72)
    signal_names = ["ret1", "z20", "micro_delta", "wall_delta", "imbalance", "spread_chg"]
    signal_results = {}

    for p in products:
        df = feat_dfs[p]
        nr = df["next_ret"]
        results = {}
        for s in signal_names:
            valid = df[[s, "next_ret"]].dropna()
            if len(valid) < 30:
                results[s] = {"corr": 0, "hit": 0.5}
                continue
            corr = valid[s].corr(valid["next_ret"])
            hit = ((np.sign(valid[s]) == np.sign(valid["next_ret"])) &
                   (valid[s] != 0) & (valid["next_ret"] != 0)).mean()
            results[s] = {"corr": corr if not np.isnan(corr) else 0,
                          "hit": hit if not np.isnan(hit) else 0.5}
        signal_results[p] = results

    # --- Plot 6A ---
    for p in products:
        fig, ax = plt.subplots(figsize=(10, 5))
        res = signal_results[p]
        sorted_sigs = sorted(signal_names, key=lambda s: abs(res[s]["corr"]))
        corrs = [res[s]["corr"] for s in sorted_sigs]
        colors = ["#d62728" if c < 0 else "#1f77b4" for c in corrs]
        ax.barh(range(len(sorted_sigs)), corrs, color=colors, edgecolor="white", alpha=0.8)
        ax.set_yticks(range(len(sorted_sigs))); ax.set_yticklabels(sorted_sigs)
        ax.axvline(0, color="black", linewidth=0.5)
        ax.set_xlabel("Correlation with next tick return")
        ax.set_title(f"{p} – Which signal best predicts next tick direction?\n"
                     f"(larger bar = higher weight in fair value formula)", fontsize=9)
        fig.tight_layout()
        savefig(fig, f"6A_signal_correlation_{p}")

    # --- Plot 6B ---
    for p in products:
        df = feat_dfs[p]
        fig, axes = plt.subplots(2, 3, figsize=(16, 9))
        axes = axes.flatten()
        res = signal_results[p]
        for i, s in enumerate(signal_names):
            ax = axes[i]
            valid = df[[s, "next_ret"]].dropna()
            if len(valid) > 3000:
                valid = valid.sample(3000, random_state=42)
            ax.scatter(valid[s], valid["next_ret"], alpha=0.1, s=3, color="#1f77b4")
            if len(valid) > 2:
                z = np.polyfit(valid[s], valid["next_ret"], 1)
                xline = np.linspace(valid[s].min(), valid[s].max(), 50)
                ax.plot(xline, np.polyval(z, xline), color="red", linewidth=1.5)
            ax.axhline(0, color="gray", linewidth=0.5)
            ax.axvline(0, color="gray", linewidth=0.5)
            ax.set_title(f"{s} corr={res[s]['corr']:.3f} hit={res[s]['hit']:.1%}",
                         fontsize=8)
            ax.set_xlabel(s); ax.set_ylabel("Next ret")
        fig.suptitle(f"Plot 6B — {p} – Signal predictive power\n"
                     f"(tight scatter around fit line = reliable signal)",
                     fontsize=10, y=1.01)
        fig.tight_layout()
        savefig(fig, f"6B_signal_scatter_{p}")

    # --- Plot 6C ---
    fig, axes = plt.subplots(1, len(products), figsize=(12 * len(products) / 2, 5),
                             squeeze=False)
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        res = signal_results[p]
        hits = [res[s]["hit"] for s in signal_names]
        colors = ["#2ca02c" if h > 0.5 else "#d62728" for h in hits]
        ax.bar(range(len(signal_names)), hits, color=colors, edgecolor="white", alpha=0.8)
        ax.set_xticks(range(len(signal_names)))
        ax.set_xticklabels(signal_names, rotation=45, ha="right", fontsize=7)
        ax.axhline(0.5, color="red", linestyle="--", linewidth=1.2, label="50% baseline")
        ax.set_ylabel("Hit Rate"); ax.set_ylim(0.3, 0.7)
        ax.set_title(f"{p} – Signal directional accuracy\n"
                     f"(above 50% = signal has edge)", fontsize=9)
        ax.legend(fontsize=7)
    fig.suptitle("Plot 6C — Hit Rate Comparison", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "6C_hit_rate_comparison")

    for p in products:
        print(f"\n  {p}:")
        print(f"    {'Signal':15s} {'Corr':>8s} {'Hit':>8s}  Recommendation")
        print(f"    {'-'*50}")
        res = signal_results[p]
        for s in sorted(signal_names, key=lambda s: abs(res[s]["corr"]), reverse=True):
            r = res[s]
            direction = "momentum" if r["corr"] > 0 else "contrarian"
            print(f"    {s:15s} {r['corr']:>8.4f} {r['hit']:>7.1%}  "
                  f"{'USE' if abs(r['corr']) > 0.02 else 'skip'} ({direction})")
    print()
    return signal_results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 7 — ARE THERE EXPLOITABLE BOT PATTERNS?
# ═══════════════════════════════════════════════════════════════════════
def section7(products, feat_dfs, trade_dfs):
    print("=" * 72)
    print("SECTION 7 — ARE THERE EXPLOITABLE BOT PATTERNS?")
    print("=" * 72)

    for p in products:
        df = feat_dfs[p]
        if p not in trade_dfs or len(trade_dfs[p]) == 0:
            print(f"  {p}: No trade data available, skipping.")
            continue
        tdf = trade_dfs[p]

        # Merge wall_mid onto trades by nearest timestamp
        wall_mid_series = df.set_index("timestamp")["wall_mid"]
        mid_series = df.set_index("timestamp")["mid_price"]

        tdf = tdf.copy()
        tdf["wall_mid"] = tdf["timestamp"].map(
            lambda t: wall_mid_series.iloc[wall_mid_series.index.searchsorted(t, side="right") - 1]
            if wall_mid_series.index.searchsorted(t, side="right") > 0 else np.nan)
        tdf["mid_at_trade"] = tdf["timestamp"].map(
            lambda t: mid_series.iloc[mid_series.index.searchsorted(t, side="right") - 1]
            if mid_series.index.searchsorted(t, side="right") > 0 else np.nan)

        # --- Plot 7A ---
        fig, ax = plt.subplots(figsize=(14, 6))
        dist = (tdf["price"] - tdf["wall_mid"]).abs()
        spread_mean = df["spread"].mean()
        colors = np.where(tdf["price"] > tdf["wall_mid"] + spread_mean, "orange",
                 np.where(tdf["price"] < tdf["wall_mid"] - spread_mean, "red", "green"))
        ax.scatter(tdf["timestamp"], tdf["price"], c=colors, s=15, alpha=0.6,
                   edgecolors="none")
        ax.plot(df["timestamp"], df["wall_mid"], color="black", linewidth=0.8,
                alpha=0.6, label="Wall Mid")
        ax.set_title(f"{p} – Bot trade prices vs fair value:\n"
                     f"orange/red dots = exploitable bot behaviour", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Trade Price")
        ax.legend(fontsize=7)
        # Legend patches
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='green', label='Near FV'),
                           Patch(facecolor='orange', label='Overbidding'),
                           Patch(facecolor='red', label='Underselling')]
        ax.legend(handles=legend_elements + [plt.Line2D([0], [0], color='black',
                  label='Wall Mid')], fontsize=7)
        fig.tight_layout()
        savefig(fig, f"7A_bot_trade_prices_{p}")

        # --- Plot 7B ---
        fig, ax = plt.subplots(figsize=(10, 5))
        qtys = tdf["quantity"].dropna()
        ax.hist(qtys, bins=max(10, int(qtys.max() - qtys.min() + 1)),
                color="#5599dd", edgecolor="white", alpha=0.8)
        top_sizes = qtys.value_counts().head(5)
        for sz, cnt in top_sizes.items():
            ax.annotate(f"qty={sz} (n={cnt})", xy=(sz, cnt),
                        fontsize=7, ha="center", va="bottom",
                        bbox=dict(boxstyle="round,pad=0.2", fc="lightyellow", ec="orange"))
        ax.set_title(f"{p} – Trade size distribution:\n"
                     f"recurring sizes = likely bot fixed-size orders", fontsize=9)
        ax.set_xlabel("Quantity"); ax.set_ylabel("Frequency")
        fig.tight_layout()
        savefig(fig, f"7B_trade_sizes_{p}")

        # --- Plot 7C ---
        fig, ax = plt.subplots(figsize=(12, 5))
        bins = np.arange(0, tdf["timestamp"].max() + 5000, 5000)
        counts, bin_edges = np.histogram(tdf["timestamp"], bins=bins)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        norm_counts = counts / counts.max() if counts.max() > 0 else counts
        colors_bar = plt.cm.YlOrRd(norm_counts)
        ax.bar(bin_centers, counts, width=4500, color=colors_bar, edgecolor="none")
        ax.axvline(140000, color="blue", linestyle="--", linewidth=1.2,
                   label="Late session (140k)")
        ax.set_title(f"{p} – When do bots trade most?\n"
                     f"(cluster before 140k = early edge, after = end-of-day)", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Trade Count")
        ax.legend(fontsize=7)
        fig.tight_layout()
        savefig(fig, f"7C_trade_timing_{p}")

        # --- Plot 7D ---
        fig, ax = plt.subplots(figsize=(12, 5))
        tdf_valid = tdf.dropna(subset=["mid_at_trade"])
        tdf_valid = tdf_valid.copy()
        tdf_valid["buyer_init"] = tdf_valid["price"] >= tdf_valid["mid_at_trade"]
        bin_idx = np.digitize(tdf_valid["timestamp"], bins) - 1
        bin_idx = np.clip(bin_idx, 0, len(bins) - 2)
        tdf_valid["bin"] = bin_idx
        buy_counts = tdf_valid.groupby("bin")["buyer_init"].sum()
        sell_counts = tdf_valid.groupby("bin")["buyer_init"].apply(lambda x: (~x).sum())
        all_bins = range(len(bins) - 1)
        bc = [buy_counts.get(b, 0) for b in all_bins]
        sc = [sell_counts.get(b, 0) for b in all_bins]
        ax.bar(bin_centers, bc, width=4500, color="green", alpha=0.7, label="Buyer-initiated")
        ax.bar(bin_centers, sc, width=4500, bottom=bc, color="red", alpha=0.7,
               label="Seller-initiated")
        ax.set_title(f"{p} – Trade direction over time:\n"
                     f"persistent green = buying pressure, red = selling pressure",
                     fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Trade Count")
        ax.legend(fontsize=7)
        fig.tight_layout()
        savefig(fig, f"7D_buyer_seller_{p}")

        # --- Plot 7E ---
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        ax1.plot(df["timestamp"], df["mid_price"], alpha=0.6, linewidth=0.5,
                 color="#1f77b4", label="Mid Price")
        ax1.scatter(tdf["timestamp"], tdf["price"], s=5, alpha=0.3, color="red",
                    label="Trades", zorder=3)
        ax1.set_ylabel("Price"); ax1.legend(fontsize=7)

        # Rolling trade count over timestamp windows
        trade_ts = tdf["timestamp"].sort_values().values
        ts_range = df["timestamp"].values
        trade_count = np.array([((trade_ts >= t - 1000) & (trade_ts <= t)).sum()
                                for t in ts_range[::10]])
        ts_sampled = ts_range[::10]
        ax2_twin = ax2.twinx()
        ax2.bar(ts_sampled, trade_count, width=800, color="orange", alpha=0.5,
                label="Trade count (1000-tick window)")
        ax2_twin.plot(df["timestamp"], df["mid_price"], alpha=0.5, linewidth=0.5,
                      color="#1f77b4", label="Mid Price")
        ax2.set_xlabel("Timestamp"); ax2.set_ylabel("Trade Count")
        ax2_twin.set_ylabel("Mid Price")
        ax2.legend(fontsize=7, loc="upper left")
        ax2_twin.legend(fontsize=7, loc="upper right")

        fig.suptitle(f"Plot 7E — {p} – Do trade bursts predict price moves?\n"
                     f"(burst before a move = order flow signal)", fontsize=10, y=1.01)
        fig.tight_layout()
        savefig(fig, f"7E_trade_clustering_{p}")

        # --- Print summary ---
        top_sizes_str = ", ".join([f"{sz}(n={cnt})" for sz, cnt in
                                   qtys.value_counts().head(3).items()])
        buyer_ratio = tdf_valid["buyer_init"].mean() if len(tdf_valid) > 0 else 0.5
        print(f"  {p:15s}  trades={len(tdf)}  top_sizes=[{top_sizes_str}]  "
              f"buyer_ratio={buyer_ratio:.1%}")
    print()


# ═══════════════════════════════════════════════════════════════════════
# SECTION 8 — SPIKE DETECTION
# ═══════════════════════════════════════════════════════════════════════
def section8(products, feat_dfs):
    print("=" * 72)
    print("SECTION 8 — SPIKE DETECTION: IS REVERSION TRADING VIABLE?")
    print("=" * 72)
    spike_results = {}

    for p in products:
        df = feat_dfs[p]

        # --- Plot 8A ---
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        ax1.plot(df["timestamp"], df["mid_price"], alpha=0.7, linewidth=0.5,
                 color="#1f77b4", label="Mid Price")
        # Spike markers
        up_spikes = df[df["spike"] & (df["ret"] > 0)]
        dn_spikes = df[df["spike"] & (df["ret"] < 0)]
        ax1.scatter(up_spikes["timestamp"], up_spikes["mid_price"],
                    marker="v", color="red", s=30, alpha=0.7, label="Up spike (sell)")
        ax1.scatter(dn_spikes["timestamp"], dn_spikes["mid_price"],
                    marker="^", color="green", s=30, alpha=0.7, label="Down spike (buy)")
        ax1.set_ylabel("Mid Price"); ax1.legend(fontsize=7)

        ax2.plot(df["timestamp"], df["rolling_vol"], alpha=0.7, linewidth=0.5,
                 color="#ff7f0e", label="Rolling 10-tick vol")
        mean_vol = df["rolling_vol"].mean()
        ax2.axhline(3 * mean_vol, color="red", linestyle="--", linewidth=1,
                    label=f"3x mean vol = {3 * mean_vol:.3f}")
        ax2.set_ylabel("Rolling Vol"); ax2.set_xlabel("Timestamp")
        ax2.legend(fontsize=7)

        n_spikes = df["spike"].sum()
        n_ticks = len(df)
        fig.suptitle(f"Plot 8A — {p} – Spike detection (threshold=3x rolling vol):\n"
                     f"triangles = mean reversion entries "
                     f"({n_spikes} spikes in {n_ticks} ticks)", fontsize=10, y=1.01)
        fig.tight_layout()
        savefig(fig, f"8A_spike_detection_{p}")

        # --- Plot 8B — Post-spike reversion ---
        fig, ax = plt.subplots(figsize=(12, 6))
        horizon = 10
        up_idx = up_spikes.index.tolist()
        dn_idx = dn_spikes.index.tolist()

        for label, indices, color in [("After UP spike", up_idx, "red"),
                                       ("After DOWN spike", dn_idx, "green")]:
            paths = []
            for i in indices:
                if i + horizon < len(df):
                    future = df["mid_price"].iloc[i:i + horizon + 1].values
                    cum_ret = future - future[0]
                    paths.append(cum_ret)
            if len(paths) > 2:
                paths = np.array(paths)
                mean_path = paths.mean(axis=0)
                std_path = paths.std(axis=0)
                x = range(horizon + 1)
                ax.plot(x, mean_path, color=color, linewidth=2, label=label)
                ax.fill_between(x, mean_path - std_path, mean_path + std_path,
                                alpha=0.15, color=color)
            else:
                ax.annotate(f"Too few {label} events ({len(paths)})",
                            xy=(0.3, 0.5), xycoords="axes fraction", fontsize=10)

        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_xlabel("Ticks after spike"); ax.set_ylabel("Cumulative return from spike")
        ax.set_title(f"{p} – Average price path after a spike:\n"
                     f"downward slope after up-spike → reversion confirmed → trade it",
                     fontsize=9)
        ax.legend(fontsize=8)
        fig.tight_layout()
        savefig(fig, f"8B_spike_reversion_{p}")

        # Stats
        spike_per_10k = n_spikes / max(1, n_ticks) * 10000
        avg_mag = df.loc[df["spike"], "ret"].abs().mean() if n_spikes > 0 else 0

        # Avg reversion within 5 ticks
        rev_5 = []
        for i in up_idx:
            if i + 5 < len(df):
                rev_5.append(df["mid_price"].iloc[i + 5] - df["mid_price"].iloc[i])
        avg_rev_up = np.mean(rev_5) if rev_5 else 0

        rev_5_dn = []
        for i in dn_idx:
            if i + 5 < len(df):
                rev_5_dn.append(df["mid_price"].iloc[i + 5] - df["mid_price"].iloc[i])
        avg_rev_dn = np.mean(rev_5_dn) if rev_5_dn else 0

        reversion_ok = (avg_rev_up < 0 and len(up_idx) > 5) or \
                       (avg_rev_dn > 0 and len(dn_idx) > 5)
        verdict = "YES — reversion confirmed" if reversion_ok else "NO — insufficient evidence"

        spike_results[p] = {"freq_per_10k": spike_per_10k, "avg_mag": avg_mag,
                            "reversion": reversion_ok}
        print(f"  {p:15s}  spikes/10k={spike_per_10k:.1f}  avg_mag={avg_mag:.3f}  "
              f"avg_rev_up_5={avg_rev_up:.3f}  avg_rev_dn_5={avg_rev_dn:.3f}  "
              f"→ {verdict}")
    print()
    return spike_results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 9 — POSITION RISK
# ═══════════════════════════════════════════════════════════════════════
def section9(products, feat_dfs, spread_results):
    print("=" * 72)
    print("SECTION 9 — POSITION RISK: WILL I HIT THE LIMIT?")
    print("=" * 72)
    pos_results = {}

    for p in products:
        df = feat_dfs[p]
        te = spread_results.get(p, {}).get("take_edge", 1.0)
        limit = 80

        # Simulate market making
        position = 0
        positions = []
        fv = df["wall_mid"].values
        ask1 = df["ask_price_1"].values
        bid1 = df["bid_price_1"].values
        ask_v1 = df["ask_volume_1"].fillna(0).values
        bid_v1 = df["bid_volume_1"].fillna(0).values

        for i in range(len(df)):
            if ask1[i] < fv[i] - te and position < limit:
                qty = min(int(ask_v1[i]), limit - position, 5)
                position += qty
            if bid1[i] > fv[i] + te and position > -limit:
                qty = min(int(bid_v1[i]), limit + position, 5)
                position -= qty
            positions.append(position)
        positions = np.array(positions)

        # --- Plot 9A ---
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(df["timestamp"], positions, alpha=0.7, linewidth=0.5, color="#1f77b4")
        ax.axhline(limit, color="red", linestyle="--", linewidth=1, label=f"+{limit} hard limit")
        ax.axhline(-limit, color="red", linestyle="--", linewidth=1, label=f"-{limit} hard limit")
        ax.axhline(60, color="orange", linestyle=":", linewidth=1, label="+60 warning")
        ax.axhline(-60, color="orange", linestyle=":", linewidth=1, label="-60 warning")
        outside = (positions > 60) | (positions < -60)
        ax.fill_between(df["timestamp"], -limit, limit,
                        where=outside, alpha=0.1, color="red")
        ax.set_title(f"{p} – Simulated position (take_edge={te:.2f}):\n"
                     f"red zones = limit breach risk", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Position")
        ax.legend(fontsize=7)
        fig.tight_layout()
        savefig(fig, f"9A_simulated_position_{p}")

        # --- Plot 9B ---
        fig, ax = plt.subplots(figsize=(10, 6))
        price_dev = df["mid_price"] - df["mid_price"].mean()
        step = max(1, len(df) // 3000)
        ax.scatter(price_dev.iloc[::step], positions[::step],
                   alpha=0.2, s=5, color="#1f77b4")
        corr_pp = np.corrcoef(price_dev.dropna(), positions[:len(price_dev.dropna())])[0, 1]
        ax.set_title(f"{p} – Position vs price deviation (corr={corr_pp:.3f}):\n"
                     f"(if correlated = adverse selection → add inventory skew)",
                     fontsize=9)
        ax.set_xlabel("Mid Price − Mean"); ax.set_ylabel("Simulated Position")
        ax.axhline(0, color="gray", linewidth=0.5)
        ax.axvline(0, color="gray", linewidth=0.5)
        fig.tight_layout()
        savefig(fig, f"9B_position_vs_price_{p}")

        # --- Plot 9C ---
        fig, ax = plt.subplots(figsize=(10, 5))
        # Find unwind times
        unwind_times = []
        i = 0
        abs_pos = np.abs(positions)
        while i < len(positions):
            if abs_pos[i] >= limit * 0.9:
                j = i + 1
                while j < len(positions) and abs_pos[j] > limit * 0.5:
                    j += 1
                if j < len(positions):
                    unwind_times.append(j - i)
                i = j
            else:
                i += 1
        if len(unwind_times) > 0:
            ax.hist(unwind_times, bins=max(10, len(set(unwind_times))),
                    color="#5599dd", edgecolor="white", alpha=0.8)
            avg_unwind = np.mean(unwind_times)
            ax.axvline(avg_unwind, color="red", linestyle="--",
                       label=f"Avg unwind = {avg_unwind:.0f} ticks")
            ax.legend(fontsize=7)
        else:
            ax.annotate("No limit breaches detected — position well controlled",
                        xy=(0.3, 0.5), xycoords="axes fraction", fontsize=10)
        ax.set_title(f"{p} – Position unwind speed:\n"
                     f"(long unwind = set WARNING earlier)", fontsize=9)
        ax.set_xlabel("Ticks to unwind from limit to 50%"); ax.set_ylabel("Frequency")
        fig.tight_layout()
        savefig(fig, f"9C_unwind_time_{p}")

        pct_at_limit = (abs_pos >= limit * 0.9).mean() * 100
        avg_unwind_t = np.mean(unwind_times) if unwind_times else 0
        warn_level = 50 if pct_at_limit > 5 else 60
        soft_cap = 40 if pct_at_limit > 10 else 50

        pos_results[p] = {"pct_at_limit": pct_at_limit, "avg_unwind": avg_unwind_t,
                          "warning": warn_level, "soft_cap": soft_cap}
        print(f"  {p:15s}  %_at_limit={pct_at_limit:.1f}%  "
              f"avg_unwind={avg_unwind_t:.0f}ticks  "
              f"WARNING={warn_level}  SOFT_CAP={soft_cap}")
    print()
    return pos_results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 10 — MULTI-PRODUCT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════
def section10(products, feat_dfs):
    print("=" * 72)
    print("SECTION 10 — MULTI-PRODUCT: ARE PRODUCTS RELATED?")
    print("=" * 72)

    if len(products) < 2:
        print("  Only one product — skipping multi-product analysis.\n")
        return {}

    # Build aligned return matrix
    # Align on (day, timestamp)
    ret_dict = {}
    for p in products:
        df = feat_dfs[p]
        s = df.set_index(["day", "timestamp"])["mid_price"]
        ret_dict[p] = s

    aligned = pd.DataFrame(ret_dict).dropna()
    rets = aligned.diff().dropna()

    # --- Plot 10A ---
    fig, ax = plt.subplots(figsize=(14, 6))
    for idx, p in enumerate(products):
        normed = (aligned[p] - aligned[p].mean()) / aligned[p].std()
        ax.plot(normed.values, alpha=0.7, linewidth=0.6,
                color=DAY_COLORS[idx % len(DAY_COLORS)], label=p)
    ax.set_title("All products – Do any move together?\n"
                 "(overlapping lines = correlated = potential pairs trade)", fontsize=10)
    ax.set_xlabel("Tick Index (aligned)"); ax.set_ylabel("Normalised Price (z-score)")
    ax.legend()
    fig.tight_layout()
    savefig(fig, "10A_normalised_prices")

    # --- Plot 10B ---
    corr_mat = rets.corr()
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(corr_mat.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(products))); ax.set_xticklabels(products, rotation=45, ha="right")
    ax.set_yticks(range(len(products))); ax.set_yticklabels(products)
    for i in range(len(products)):
        for j in range(len(products)):
            ax.text(j, i, f"{corr_mat.iloc[i, j]:.3f}", ha="center", va="center",
                    fontsize=10, color="white" if abs(corr_mat.iloc[i, j]) > 0.5 else "black")
    plt.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title("Product return correlation matrix:\n"
                 "above 0.7 = strong enough for pairs trading", fontsize=10)
    fig.tight_layout()
    savefig(fig, "10B_correlation_matrix")

    # --- Plot 10C — Lead-lag ---
    pairs = list(itertools.combinations(products, 2))
    n_pairs = len(pairs)
    if n_pairs > 0:
        fig, axes = plt.subplots(1, n_pairs, figsize=(10 * n_pairs, 5), squeeze=False)
        lag_range = range(-5, 6)
        for idx, (p1, p2) in enumerate(pairs):
            ax = axes[0, idx]
            r1 = rets[p1].values
            r2 = rets[p2].values
            xcorrs = [np.corrcoef(r1[:len(r1) - abs(l)] if l >= 0 else r1[abs(l):],
                                  r2[abs(l):] if l >= 0 else r2[:len(r2) - abs(l)])[0, 1]
                      for l in lag_range]
            colors = ["#1f77b4" if abs(x) > 0.05 else "#cccccc" for x in xcorrs]
            ax.bar(list(lag_range), xcorrs, color=colors, edgecolor="white")
            ax.axhline(0, color="black", linewidth=0.5)
            ax.set_xlabel(f"Lag (positive = {p1} leads)")
            ax.set_ylabel("Cross-correlation")
            ax.set_title(f"{p1} vs {p2} – Lead-lag relationship:\n"
                         f"non-zero lag peak = one leads → trade follower", fontsize=9)
        fig.tight_layout()
        savefig(fig, "10C_lead_lag")

    print("\n  Correlation matrix:")
    print(corr_mat.to_string(float_format=lambda x: f"{x:.4f}"))
    strong_pairs = [(p1, p2, corr_mat.loc[p1, p2])
                    for p1, p2 in pairs if abs(corr_mat.loc[p1, p2]) > 0.5]
    if strong_pairs:
        print(f"\n  Strong correlations (>0.5): {strong_pairs}")
    else:
        print("\n  No pairs with correlation above 0.5.")
    print()
    return {"corr_mat": corr_mat}


# ═══════════════════════════════════════════════════════════════════════
# SECTION 11 — STRATEGY DECISION DASHBOARD
# ═══════════════════════════════════════════════════════════════════════
def section11(products, feat_dfs, verdicts, fv_results, spread_results,
              acf_results, signal_results, spike_results, pos_results):
    print("=" * 72)
    print("SECTION 11 — STRATEGY DECISION DASHBOARD")
    print("=" * 72)

    strat_map = {"STABLE": "Fixed FV Market Making",
                 "DRIFTING": "Dynamic FV Market Making",
                 "VOLATILE": "Spike Reversion + Wide MM"}

    for p in products:
        df = feat_dfs[p]
        v = verdicts.get(p, "STABLE")
        sr = spread_results.get(p, {})
        acf = acf_results.get(p, {})
        sig = signal_results.get(p, {})
        spk = spike_results.get(p, {})
        fv = fv_results.get(p, {})
        pos = pos_results.get(p, {})

        fig, axes = plt.subplots(3, 3, figsize=(22, 18))

        # [0,0] Price history + mean
        ax = axes[0, 0]
        days = sorted(df["day"].unique())
        for di, day in enumerate(days):
            dd = df[df["day"] == day]
            ax.plot(dd["timestamp"], dd["mid_price"],
                    color=DAY_COLORS[di % len(DAY_COLORS)], alpha=0.7, linewidth=0.5)
        ax.axhline(df["mid_price"].mean(), color="black", linestyle="--", linewidth=1)
        ax.set_title(f"Price History → {v}", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Price")

        # [0,1] Autocorrelation bars
        ax = axes[0, 1]
        lags = [1, 2, 3, 5, 10]
        rets = df["ret"].dropna()
        acfs_vals = [rets.autocorr(lag=l) for l in lags]
        colors = ["#d62728" if a < 0 else "#1f77b4" for a in acfs_vals]
        ax.bar(range(len(lags)), acfs_vals, color=colors, edgecolor="white")
        ax.set_xticks(range(len(lags))); ax.set_xticklabels([str(l) for l in lags])
        ax.axhline(0, color="black", linewidth=0.5)
        ax.axhline(0.05, color="gray", linestyle=":", linewidth=0.7)
        ax.axhline(-0.05, color="gray", linestyle=":", linewidth=0.7)
        mr_label = "Mean Reverting" if acfs_vals[0] < -0.05 else (
            "Trending" if acfs_vals[0] > 0.05 else "Neutral")
        ax.set_title(f"Autocorrelation → {mr_label}", fontsize=9)
        ax.set_xlabel("Lag"); ax.set_ylabel("ACF")

        # [0,2] Z-score
        ax = axes[0, 2]
        ax.plot(df["timestamp"], df["z20"], alpha=0.7, linewidth=0.5, color="#ff7f0e")
        ax.axhline(1, color="gray", linestyle="--", linewidth=0.7)
        ax.axhline(-1, color="gray", linestyle="--", linewidth=0.7)
        ax.axhline(2, color="red", linestyle=":", linewidth=0.7)
        ax.axhline(-2, color="red", linestyle=":", linewidth=0.7)
        ax.axhline(0, color="black", linewidth=0.5)
        z_max = df["z20"].abs().quantile(0.99)
        ax.set_title(f"Z-Score (99th pctl |z|={z_max:.1f})", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Z-Score")

        # [1,0] Spread distribution
        ax = axes[1, 0]
        sp = df["spread"].dropna()
        ax.hist(sp, bins=50, color="#5599dd", edgecolor="white", alpha=0.8)
        te = sr.get("take_edge", 1)
        pe = sr.get("passive_edge", 1)
        ax.axvline(sp.median(), color="orange", linestyle="--", linewidth=1,
                   label=f"Median={sp.median():.1f}")
        ax.set_title(f"Spread Dist (TE={te:.2f}, PE={pe:.2f})", fontsize=9)
        ax.set_xlabel("Spread"); ax.set_ylabel("Freq")
        ax.legend(fontsize=7)

        # [1,1] Signal correlation bars
        ax = axes[1, 1]
        signal_names = ["ret1", "z20", "micro_delta", "wall_delta", "imbalance", "spread_chg"]
        if sig:
            sorted_sigs = sorted(signal_names, key=lambda s: abs(sig.get(s, {}).get("corr", 0)))
            corrs = [sig.get(s, {}).get("corr", 0) for s in sorted_sigs]
            colors_s = ["#d62728" if c < 0 else "#1f77b4" for c in corrs]
            ax.barh(range(len(sorted_sigs)), corrs, color=colors_s, edgecolor="white")
            ax.set_yticks(range(len(sorted_sigs)))
            ax.set_yticklabels(sorted_sigs, fontsize=7)
            best_sig = sorted_sigs[-1]
            ax.set_title(f"Signals → Best: {best_sig}", fontsize=9)
        else:
            ax.set_title("Signals (no data)", fontsize=9)
        ax.axvline(0, color="black", linewidth=0.5)
        ax.set_xlabel("Corr with next ret")

        # [1,2] Spike detection
        ax = axes[1, 2]
        ax.plot(df["timestamp"], df["mid_price"], alpha=0.6, linewidth=0.5, color="#1f77b4")
        up_sp = df[df["spike"] & (df["ret"] > 0)]
        dn_sp = df[df["spike"] & (df["ret"] < 0)]
        ax.scatter(up_sp["timestamp"], up_sp["mid_price"], marker="v", color="red",
                   s=20, alpha=0.7)
        ax.scatter(dn_sp["timestamp"], dn_sp["mid_price"], marker="^", color="green",
                   s=20, alpha=0.7)
        spike_verdict = "YES" if spk.get("reversion", False) else "NO"
        ax.set_title(f"Spikes → Reversion viable: {spike_verdict}", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Price")

        # [2,0] Wall quote scatter (sampled)
        ax = axes[2, 0]
        step = max(1, len(df) // 2000)
        ds = df.iloc[::step]
        ax.scatter(ds["timestamp"], ds["bid_wall_price"], s=3, alpha=0.3, color="blue",
                   label="Bid wall")
        ax.scatter(ds["timestamp"], ds["ask_wall_price"], s=3, alpha=0.3, color="red",
                   label="Ask wall")
        ax.plot(ds["timestamp"], ds["wall_mid"], color="black", linewidth=0.8, alpha=0.7,
                label="Wall mid")
        best_fv = min(fv, key=fv.get).replace("_std", "") if fv else "wall_mid"
        ax.set_title(f"Wall Quotes → Best FV: {best_fv}", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Price")
        ax.legend(fontsize=6)

        # [2,1] Simulated position
        ax = axes[2, 1]
        # Quick re-sim for dashboard
        position = 0; positions_d = []
        fv_arr = df["wall_mid"].values
        a1 = df["ask_price_1"].values; b1 = df["bid_price_1"].values
        av1 = df["ask_volume_1"].fillna(0).values; bv1 = df["bid_volume_1"].fillna(0).values
        for i in range(len(df)):
            if a1[i] < fv_arr[i] - te and position < 80:
                position += min(int(av1[i]), 80 - position, 5)
            if b1[i] > fv_arr[i] + te and position > -80:
                position -= min(int(bv1[i]), 80 + position, 5)
            positions_d.append(position)
        positions_d = np.array(positions_d)
        ax.plot(df["timestamp"], positions_d, alpha=0.7, linewidth=0.5, color="#1f77b4")
        ax.axhline(80, color="red", linestyle="--", linewidth=0.8)
        ax.axhline(-80, color="red", linestyle="--", linewidth=0.8)
        ax.axhline(60, color="orange", linestyle=":", linewidth=0.7)
        ax.axhline(-60, color="orange", linestyle=":", linewidth=0.7)
        pct_lim = (np.abs(positions_d) >= 72).mean() * 100
        ax.set_title(f"Sim Position (at limit {pct_lim:.1f}%)", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Position")

        # [2,2] Text box: FINAL RECOMMENDATION
        ax = axes[2, 2]
        ax.axis("off")

        # Determine best signal
        if sig:
            best_signal = max(signal_names,
                              key=lambda s: abs(sig.get(s, {}).get("corr", 0)))
            best_corr = sig[best_signal]["corr"]
        else:
            best_signal = "N/A"; best_corr = 0

        bot_detected = "YES" if spk.get("freq_per_10k", 0) > 10 else "NO"

        rec_text = (
            f"━━━━━ FINAL RECOMMENDATION ━━━━━\n\n"
            f"Product type    : {v}\n"
            f"Primary strategy: {strat_map.get(v, 'MM')}\n"
            f"Fair value      : {best_fv}\n"
            f"Take edge       : {te:.2f}\n"
            f"Passive edge    : {pe:.2f}\n"
            f"Key signal      : {best_signal} (corr={best_corr:.3f})\n"
            f"Spike reversion : {spike_verdict}\n"
            f"Bot pattern     : {bot_detected}\n"
            f"Pos WARNING     : {pos.get('warning', 60)}\n"
            f"Pos SOFT_CAP    : {pos.get('soft_cap', 50)}"
        )
        ax.text(0.05, 0.95, rec_text, transform=ax.transAxes,
                fontsize=11, verticalalignment="top", fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.5", fc="#ffffdd", ec="#cc8800",
                          linewidth=2))

        fig.suptitle(f"{p} – Full Strategy Decision Dashboard", fontsize=14, y=1.01)
        fig.tight_layout()
        savefig(fig, f"11_dashboard_{p}")

        # Print final summary
        print(f"\n  ╔══════════════════════════════════════════════════╗")
        print(f"  ║  {p:^46s}  ║")
        print(f"  ╠══════════════════════════════════════════════════╣")
        print(f"  ║  Type            : {v:<28s}  ║")
        print(f"  ║  Strategy        : {strat_map.get(v, 'MM'):<28s}  ║")
        print(f"  ║  Fair Value      : {best_fv:<28s}  ║")
        print(f"  ║  Take Edge       : {te:<28.2f}  ║")
        print(f"  ║  Passive Edge    : {pe:<28.2f}  ║")
        print(f"  ║  Key Signal      : {best_signal + f' ({best_corr:.3f})':<28s}  ║")
        print(f"  ║  Spike Reversion : {spike_verdict:<28s}  ║")
        print(f"  ║  Bot Pattern     : {bot_detected:<28s}  ║")
        print(f"  ║  WARNING level   : {pos.get('warning', 60):<28}  ║")
        print(f"  ║  SOFT_CAP        : {pos.get('soft_cap', 50):<28}  ║")
        print(f"  ╚══════════════════════════════════════════════════╝")
    print()


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════
def main():
    print("\n" + "█" * 72)
    print("█  IMC PROSPERITY 4 — VISUAL MARKET ANALYSIS TOOL")
    print("█" * 72 + "\n")

    # Section 1
    products, product_dfs, trade_dfs = load_data()

    # Compute features
    feat_dfs = {p: compute_features(product_dfs[p]) for p in products}

    # Section 2
    verdicts = section2(products, feat_dfs)

    # Section 3
    fv_results = section3(products, feat_dfs)

    # Section 4
    spread_results = section4(products, feat_dfs)

    # Section 5
    acf_results = section5(products, feat_dfs)

    # Section 6
    signal_results = section6(products, feat_dfs)

    # Section 7
    section7(products, feat_dfs, trade_dfs)

    # Section 8
    spike_results = section8(products, feat_dfs)

    # Section 9
    pos_results = section9(products, feat_dfs, spread_results)

    # Section 10
    section10(products, feat_dfs)

    # Section 11
    section11(products, feat_dfs, verdicts, fv_results, spread_results,
              acf_results, signal_results, spike_results, pos_results)

    print(f"\n{'=' * 72}")
    print(f"ALL PLOTS SAVED TO: {PLOT_DIR}/")
    print(f"{'=' * 72}\n")


if __name__ == "__main__":
    main()
