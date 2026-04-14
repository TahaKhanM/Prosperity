#!/usr/bin/env python3
"""
IMC Prosperity 4 — Round 1 Market Analysis Tool (V2)
=====================================================
Restructured based on top-10 team approaches from Prosperity 3.
Each section answers a specific strategy question.

Products:
  ASH_COATED_OSMIUM  — described as "volatile" but data shows CV~0.0005 within-day,
                       mean anchored at ~10,000. "Hidden pattern" = subtle oscillation.
  INTARIAN_PEPPER_ROOT — described as "steady" but drifts ~1000/day upward.
                          Within-day CV~0.025, range ~1000 units per day.

Round 1 data notes:
  - buyer/seller columns are EMPTY (no counterparty IDs available)
  - Book depth: level 2 ~65% populated, level 3 ~2% populated
  - ~4% of ticks have empty book (bid or ask missing), filtered out

Run:  python analysis.py          (from the data directory)
Also: analysis.ipynb              (same code, cell-by-cell)
"""

import glob, os, warnings, itertools
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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

# Position limits for Round 1
POSITION_LIMITS = {
    "ASH_COATED_OSMIUM": 80,
    "INTARIAN_PEPPER_ROOT": 80,
}
DEFAULT_LIMIT = 80

MM_SIZE_THRESHOLD = 10  # Orders >= this size are likely market-maker quotes


def savefig(fig, name):
    fig.savefig(os.path.join(PLOT_DIR, f"{name}.png"), bbox_inches="tight")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# SECTION 0 — DATA LOADING
# ═══════════════════════════════════════════════════════════════════════
def load_data():
    """Auto-detect and load all price and trade CSVs."""
    base = os.path.dirname(os.path.abspath(__file__))
    price_files = sorted(glob.glob(os.path.join(base, "prices_round_*_day_*.csv")))
    trade_files = sorted(glob.glob(os.path.join(base, "trades_round_*_day_*.csv")))

    prices = pd.concat([pd.read_csv(f, sep=";") for f in price_files], ignore_index=True)
    trades = pd.concat([pd.read_csv(f, sep=";") for f in trade_files], ignore_index=True)

    num_cols = [c for c in prices.columns if c not in ("product",)]
    for c in num_cols:
        prices[c] = pd.to_numeric(prices[c], errors="coerce")
    for c in ["price", "quantity", "timestamp"]:
        if c in trades.columns:
            trades[c] = pd.to_numeric(trades[c], errors="coerce")

    if "symbol" in trades.columns:
        trades = trades.rename(columns={"symbol": "product"})

    # Filter out empty book rows (mid_price == 0 or bid/ask missing)
    prices = prices[(prices["mid_price"] > 0) &
                    prices["bid_price_1"].notna() &
                    prices["ask_price_1"].notna()].reset_index(drop=True)

    products = sorted(prices["product"].unique())
    product_dfs = {p: prices[prices["product"] == p].copy().reset_index(drop=True)
                   for p in products}
    trade_dfs = {p: trades[trades["product"] == p].copy().reset_index(drop=True)
                 for p in products if p in trades["product"].unique()}

    print("=" * 72)
    print("SECTION 0 — DATA LOADING SUMMARY")
    print("=" * 72)
    print(f"Price files loaded : {len(price_files)}")
    print(f"Trade files loaded : {len(trade_files)}")
    print(f"Total price rows   : {len(prices):,}")
    print(f"Total trade rows   : {len(trades):,}")
    print(f"Products           : {products}")
    print(f"Days               : {sorted(prices['day'].unique())}")
    for p in products:
        df = product_dfs[p]
        print(f"  {p:30s}  rows={len(df):>6,}  "
              f"mid=[{df['mid_price'].min():.1f}, {df['mid_price'].max():.1f}]  "
              f"days={sorted(df['day'].unique())}")
    print()
    return products, product_dfs, trade_dfs


# ═══════════════════════════════════════════════════════════════════════
# HELPER — compute all derived columns
# ═══════════════════════════════════════════════════════════════════════
def compute_features(df):
    """Add all helper columns to a single-product dataframe."""
    d = df.copy()

    # Simple mid
    d["simple_mid"] = (d["bid_price_1"] + d["ask_price_1"]) / 2

    # Microprice (volume-weighted mid)
    bv1 = d["bid_volume_1"].fillna(0)
    av1 = d["ask_volume_1"].fillna(0)
    denom = bv1 + av1
    d["microprice"] = np.where(denom > 0,
        (d["bid_price_1"] * av1 + d["ask_price_1"] * bv1) / denom,
        d["simple_mid"])

    # Wall mid (price level with largest resting volume)
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

    # MM-filtered mid (only large orders >= threshold)
    mm_bid = np.full(len(d), np.nan)
    mm_ask = np.full(len(d), np.nan)
    for i in range(len(d)):
        # Find best bid among large orders
        for lvl in range(3):
            bv = bid_vols[i, lvl]
            if bv >= MM_SIZE_THRESHOLD:
                mm_bid[i] = bid_prices[i, lvl]
                break
        # Find best ask among large orders
        for lvl in range(3):
            av = ask_vols[i, lvl]
            if av >= MM_SIZE_THRESHOLD:
                mm_ask[i] = ask_prices[i, lvl]
                break
    valid_mm = ~np.isnan(mm_bid) & ~np.isnan(mm_ask)
    d["mm_mid"] = np.where(valid_mm, (mm_bid + mm_ask) / 2, d["wall_mid"])

    # Spread
    d["spread"] = d["ask_price_1"] - d["bid_price_1"]

    # Book imbalance (3-level)
    total_bid = d[["bid_volume_1", "bid_volume_2", "bid_volume_3"]].fillna(0).sum(axis=1)
    total_ask = d[["ask_volume_1", "ask_volume_2", "ask_volume_3"]].fillna(0).sum(axis=1)
    d["imbalance"] = (total_bid - total_ask) / (total_bid + total_ask).replace(0, np.nan)

    # Returns & rolling vol
    d["ret"] = d["mid_price"].diff()
    d["rolling_vol"] = d["ret"].rolling(10).std()
    d["rolling_vol_20"] = d["ret"].rolling(20).std()

    # Z-score (20-tick)
    rm20 = d["mid_price"].rolling(20).mean()
    rs20 = d["mid_price"].rolling(20).std()
    d["z20"] = (d["mid_price"] - rm20) / rs20.replace(0, np.nan)

    # Spike flag (3x rolling vol)
    d["spike"] = d["ret"].abs() > 3 * d["rolling_vol"]

    # Signals for predictiveness testing
    d["ret1"] = d["ret"]
    d["micro_delta"] = d["microprice"] - d["simple_mid"]
    d["wall_delta"] = d["wall_mid"] - d["simple_mid"]
    d["mm_delta"] = d["mm_mid"] - d["simple_mid"]
    d["spread_chg"] = d["spread"].diff()
    # Multi-horizon future returns
    for h in [1, 2, 5, 10, 20]:
        d[f"fwd_ret_{h}"] = d["mid_price"].diff(h).shift(-h)

    return d


# ═══════════════════════════════════════════════════════════════════════
# SECTION 1 — PRODUCT CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════
def classify_product_within_day(df):
    """Classify using within-day CV (not across-day, which is inflated by drift).
    Also detect drift by checking if daily means shift significantly."""
    days = sorted(df["day"].unique())

    # Within-day CV (average across days)
    day_cvs = []
    day_means = []
    for day in days:
        dd = df[df["day"] == day]["mid_price"].dropna()
        if len(dd) > 10:
            day_cvs.append(dd.std() / dd.mean())
            day_means.append(dd.mean())

    avg_cv = np.mean(day_cvs) if day_cvs else 0

    # Drift detection: check if daily means shift
    drift_per_day = 0
    if len(day_means) >= 2:
        drift_per_day = abs(np.mean(np.diff(day_means)))
        avg_mean = np.mean(day_means)
        drift_pct = drift_per_day / avg_mean if avg_mean > 0 else 0
    else:
        drift_pct = 0

    # Classification
    if avg_cv < 0.001:
        stability = "STABLE"
    elif avg_cv < 0.03:
        stability = "DRIFTING"
    else:
        stability = "VOLATILE"

    has_drift = drift_pct > 0.01  # >1% drift per day
    if has_drift:
        stability = "DRIFTING"  # Override: strong drift always = DRIFTING

    return stability, avg_cv, drift_per_day, has_drift


def section1(products, feat_dfs):
    """Classify each product using within-day CV and drift detection."""
    print("=" * 72)
    print("SECTION 1 — PRODUCT CLASSIFICATION")
    print("=" * 72)
    n = len(products)
    verdicts = {}

    # --- 1A: Price History ---
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 5), squeeze=False)
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        df = feat_dfs[p]
        days = sorted(df["day"].unique())
        for di, day in enumerate(days):
            dd = df[df["day"] == day]
            ax.plot(dd["timestamp"], dd["mid_price"],
                    color=DAY_COLORS[di % len(DAY_COLORS)],
                    alpha=0.7, linewidth=0.6, label=f"Day {day}")
        # Per-day means instead of global mean
        for di, day in enumerate(days):
            dd = df[df["day"] == day]
            day_mean = dd["mid_price"].mean()
            ax.axhline(day_mean, color=DAY_COLORS[di % len(DAY_COLORS)],
                       linestyle=":", linewidth=0.8, alpha=0.5)
        ax.set_title(f"{p}\nDo daily means shift? (drift detection)", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Mid Price")
        ax.legend(fontsize=7)
    fig.suptitle("1A — Price History (dotted = daily means)", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "1A_price_history")

    # --- 1B: Within-Day Distribution ---
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 5), squeeze=False)
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        df = feat_dfs[p]
        verdict, avg_cv, drift, has_drift = classify_product_within_day(df)
        verdicts[p] = verdict
        # Show per-day distributions
        days = sorted(df["day"].unique())
        for di, day in enumerate(days):
            dd = df[df["day"] == day]
            mid = dd["mid_price"].dropna()
            ax.hist(mid, bins=40, color=DAY_COLORS[di % len(DAY_COLORS)],
                    alpha=0.5, edgecolor="white", label=f"Day {day}")
        drift_str = f", drift={drift:.0f}/day" if has_drift else ""
        ax.set_title(f"{p} — within-day CV={avg_cv:.6f}{drift_str} → {verdict}", fontsize=9)
        ax.set_xlabel("Mid Price"); ax.set_ylabel("Frequency")
        ax.legend(fontsize=7)
    fig.suptitle("1B — Per-Day Price Distribution & Classification", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "1B_price_distribution")

    # --- 1C: Rolling Volatility ---
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 5), squeeze=False)
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
        ax.set_title(f"{p} — Constant vol or regime-switching?", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Rolling 20-tick Std")
        ax.legend(fontsize=7)
    fig.suptitle("1C — Volatility Regimes", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "1C_rolling_volatility")

    # --- 1D: Day-over-day trend ---
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 5), squeeze=False)
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        df = feat_dfs[p]
        days = sorted(df["day"].unique())
        day_means = [df[df["day"] == d]["mid_price"].mean() for d in days]
        day_stds = [df[df["day"] == d]["mid_price"].std() for d in days]
        ax.errorbar(days, day_means, yerr=day_stds, fmt="o-", capsize=5,
                    color="#1f77b4", linewidth=2, markersize=8)
        if len(days) >= 2:
            slope = np.polyfit(days, day_means, 1)[0]
            ax.annotate(f"Slope = {slope:.1f}/day",
                        xy=(0.05, 0.90), xycoords="axes fraction", fontsize=9,
                        bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="orange"))
        ax.set_title(f"{p} — Day-over-day trend", fontsize=9)
        ax.set_xlabel("Day"); ax.set_ylabel("Mean Mid Price (±1σ)")
    fig.suptitle("1D — Daily Trend Detection", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "1D_daily_trend")

    strat_map = {"STABLE": "Fixed Fair Value Market Making (anchor at ~10000)",
                 "DRIFTING": "Dynamic / Rolling Fair Value MM",
                 "VOLATILE": "Spike Reversion + Wide-edge MM"}
    for p in products:
        v, cv, drift, has_drift = classify_product_within_day(feat_dfs[p])
        drift_str = f"  drift={drift:.0f}/day" if has_drift else ""
        print(f"  {p:30s}  within-day CV={cv:.6f}{drift_str}  →  {v}  →  {strat_map[v]}")
    print()
    return verdicts


# ═══════════════════════════════════════════════════════════════════════
# SECTION 2 — FAIR VALUE ESTIMATION
# ═══════════════════════════════════════════════════════════════════════
def section2(products, feat_dfs):
    """Compare 4 fair value estimators: simple mid, microprice, wall mid, MM-filtered mid."""
    print("=" * 72)
    print("SECTION 2 — FAIR VALUE ESTIMATION")
    print("=" * 72)
    fv_results = {}

    for p in products:
        df = feat_dfs[p]

        # --- 2A: Four FV estimates overlaid ---
        fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
        ax1, ax2, ax3 = axes
        ax1.plot(df["timestamp"], df["simple_mid"], alpha=0.6, linewidth=0.5,
                 label="Simple Mid", color="#1f77b4")
        ax1.plot(df["timestamp"], df["microprice"], alpha=0.6, linewidth=0.5,
                 label="Microprice", color="#ff7f0e")
        ax1.plot(df["timestamp"], df["wall_mid"], alpha=0.6, linewidth=0.5,
                 label="Wall Mid", color="#2ca02c")
        ax1.plot(df["timestamp"], df["mm_mid"], alpha=0.6, linewidth=0.5,
                 label=f"MM-Filtered Mid (≥{MM_SIZE_THRESHOLD})", color="#d62728")
        ax1.set_ylabel("Price"); ax1.legend(fontsize=7)
        ax1.set_title(f"{p} — Which fair value estimate is most stable?", fontsize=9)

        ax2.plot(df["timestamp"], df["microprice"] - df["simple_mid"],
                 alpha=0.7, linewidth=0.5, color="#ff7f0e", label="Microprice − Mid")
        ax2.plot(df["timestamp"], df["mm_mid"] - df["simple_mid"],
                 alpha=0.7, linewidth=0.5, color="#d62728", label="MM Mid − Mid")
        ax2.axhline(0, color="black", linewidth=0.5)
        ax2.set_ylabel("Deviation from Simple Mid"); ax2.legend(fontsize=7)

        ax3.plot(df["timestamp"], df["wall_mid"] - df["simple_mid"],
                 alpha=0.7, linewidth=0.5, color="#2ca02c")
        ax3.axhline(0, color="black", linewidth=0.5)
        ax3.set_ylabel("Wall Mid − Simple Mid"); ax3.set_xlabel("Timestamp")

        fig.suptitle(f"2A — {p}: Fair Value Comparison", fontsize=12, y=1.01)
        fig.tight_layout()
        savefig(fig, f"2A_fair_value_{p}")

        # --- 2B: Wall quote scatter ---
        fig, ax = plt.subplots(figsize=(14, 6))
        step = max(1, len(df) // 4000)
        ds = df.iloc[::step]
        vol_cols_bid = ["bid_volume_1", "bid_volume_2", "bid_volume_3"]
        vol_cols_ask = ["ask_volume_1", "ask_volume_2", "ask_volume_3"]
        price_cols_bid = ["bid_price_1", "bid_price_2", "bid_price_3"]
        price_cols_ask = ["ask_price_1", "ask_price_2", "ask_price_3"]

        all_vols = np.concatenate([
            ds[vol_cols_bid].fillna(0).values.flatten(),
            ds[vol_cols_ask].fillna(0).values.flatten()])
        all_vols = all_vols[all_vols > 0]
        vol_75 = np.percentile(all_vols, 75) if len(all_vols) > 0 else 1

        for i in range(3):
            bv = ds[vol_cols_bid[i]].fillna(0)
            bp = ds[price_cols_bid[i]]
            mask = bv > 0
            sizes = np.clip(bv[mask] / vol_75 * 15, 2, 60)
            ax.scatter(ds["timestamp"][mask], bp[mask], s=sizes,
                       alpha=0.15, color="blue", edgecolors="none")
            wall_mask = mask & (bv >= MM_SIZE_THRESHOLD)
            if wall_mask.any():
                ax.scatter(ds["timestamp"][wall_mask], bp[wall_mask],
                           s=np.clip(bv[wall_mask] / vol_75 * 30, 20, 120),
                           alpha=0.5, color="blue", edgecolors="darkblue",
                           linewidth=0.5, label="MM Bid" if i == 0 else "")

            av = ds[vol_cols_ask[i]].fillna(0)
            ap = ds[price_cols_ask[i]]
            mask_a = av > 0
            sizes_a = np.clip(av[mask_a] / vol_75 * 15, 2, 60)
            ax.scatter(ds["timestamp"][mask_a], ap[mask_a], s=sizes_a,
                       alpha=0.15, color="red", edgecolors="none")
            wall_mask_a = mask_a & (av >= MM_SIZE_THRESHOLD)
            if wall_mask_a.any():
                ax.scatter(ds["timestamp"][wall_mask_a], ap[wall_mask_a],
                           s=np.clip(av[wall_mask_a] / vol_75 * 30, 20, 120),
                           alpha=0.5, color="red", edgecolors="darkred",
                           linewidth=0.5, label="MM Ask" if i == 0 else "")

        ax.plot(ds["timestamp"], ds["wall_mid"], color="black", linewidth=1,
                alpha=0.8, label="Wall Mid")
        ax.set_title(f"{p} — Order book: large dots = market-maker quotes (≥{MM_SIZE_THRESHOLD})",
                     fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Price")
        ax.legend(fontsize=7)
        fig.tight_layout()
        savefig(fig, f"2B_wall_quotes_{p}")

        # Compute FV noise
        fv_results[p] = {
            "simple_mid_std": df["simple_mid"].std(),
            "microprice_std": df["microprice"].std(),
            "wall_mid_std": df["wall_mid"].std(),
            "mm_mid_std": df["mm_mid"].std(),
        }

    # --- 2C: Stability ranking ---
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(products))
    w = 0.2
    methods = ["simple_mid_std", "microprice_std", "wall_mid_std", "mm_mid_std"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    labels = ["Simple Mid", "Microprice", "Wall Mid", f"MM-Filtered (≥{MM_SIZE_THRESHOLD})"]
    for i, (method, col, lab) in enumerate(zip(methods, colors, labels)):
        vals = [fv_results[p][method] for p in products]
        ax.bar(x + i * w, vals, w, label=lab, color=col, alpha=0.8)
    ax.set_xticks(x + 1.5 * w); ax.set_xticklabels(products)
    ax.set_ylabel("Std of Fair Value Estimate")
    ax.set_title("2C — Lowest bar = best fair value anchor", fontsize=10)
    ax.legend()
    fig.tight_layout()
    savefig(fig, "2C_fair_value_ranking")

    for p in products:
        r = fv_results[p]
        best = min(r, key=r.get).replace("_std", "")
        print(f"  {p:30s}  simple={r['simple_mid_std']:.4f}  micro={r['microprice_std']:.4f}  "
              f"wall={r['wall_mid_std']:.4f}  mm={r['mm_mid_std']:.4f}  → USE: {best}")
    print()
    return fv_results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 3 — SPREAD & EDGE CALIBRATION
# ═══════════════════════════════════════════════════════════════════════
def section3(products, feat_dfs):
    """Analyze spreads to determine take_edge and passive_edge parameters."""
    print("=" * 72)
    print("SECTION 3 — SPREAD & EDGE CALIBRATION")
    print("=" * 72)
    n = len(products)
    spread_results = {}

    # --- 3A: Spread over time ---
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 5), squeeze=False)
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
        ax.axhline(sp.mean(), color="black", linestyle="--", linewidth=1,
                   label=f"Mean={sp.mean():.2f}")
        ax.set_title(f"{p} — Spread over time", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Bid-Ask Spread")
        ax.legend(fontsize=6)
    fig.suptitle("3A — Spread Time Series", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "3A_spread_time")

    # --- 3B: Spread distribution with edge suggestions ---
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 5), squeeze=False)
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        df = feat_dfs[p]
        sp = df["spread"].dropna()
        ax.hist(sp, bins=60, color="#5599dd", edgecolor="white", alpha=0.8)
        p25, p50, p75 = sp.quantile(0.25), sp.quantile(0.5), sp.quantile(0.75)
        for pval, lab, col in [(p25, "25th", "green"), (p50, "50th", "orange"), (p75, "75th", "red")]:
            ax.axvline(pval, color=col, linestyle="--", linewidth=1.2, label=f"{lab}={pval:.1f}")
        te = p25 / 4; pe = p50 / 3
        ax.annotate(f"take_edge ≈ {te:.2f}\npassive_edge ≈ {pe:.2f}",
                    xy=(0.55, 0.80), xycoords="axes fraction", fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="orange"))
        ax.set_title(f"{p} — Spread distribution", fontsize=9)
        ax.set_xlabel("Spread"); ax.set_ylabel("Frequency")
        ax.legend(fontsize=7)
        spread_results[p] = {"mean": sp.mean(), "std": sp.std(),
                             "p25": p25, "p50": p50, "p75": p75,
                             "take_edge": te, "passive_edge": pe}
    fig.suptitle("3B — Spread Distribution & Edge Parameters", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "3B_spread_distribution")

    for p in products:
        sr = spread_results[p]
        print(f"  {p:30s}  mean={sr['mean']:.2f}  p25/p50/p75={sr['p25']:.1f}/{sr['p50']:.1f}/{sr['p75']:.1f}  "
              f"take_edge={sr['take_edge']:.2f}  passive_edge={sr['passive_edge']:.2f}")
    print()
    return spread_results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 4 — MEAN REVERSION vs TREND
# ═══════════════════════════════════════════════════════════════════════
def section4(products, feat_dfs):
    """Determine if returns are mean-reverting (good for MM) or trending."""
    print("=" * 72)
    print("SECTION 4 — MEAN REVERSION vs TREND")
    print("=" * 72)
    n = len(products)
    acf_results = {}

    # --- 4A: Autocorrelation bars ---
    lags = [1, 2, 3, 5, 10]
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 5), squeeze=False)
    for idx, p in enumerate(products):
        ax = axes[0, idx]
        df = feat_dfs[p]
        rets = df["ret"].dropna()
        acfs = [rets.autocorr(lag=l) for l in lags]
        colors = ["#d62728" if a < 0 else "#1f77b4" for a in acfs]
        ax.bar(range(len(lags)), acfs, color=colors, edgecolor="white", alpha=0.8)
        ax.set_xticks(range(len(lags))); ax.set_xticklabels([str(l) for l in lags])
        ax.axhline(0, color="black", linewidth=0.5)
        ax.axhline(0.05, color="gray", linestyle=":", linewidth=0.8)
        ax.axhline(-0.05, color="gray", linestyle=":", linewidth=0.8)
        ax.set_title(f"{p}\nRED=mean reverting  BLUE=trending", fontsize=8)
        ax.set_xlabel("Lag"); ax.set_ylabel("Autocorrelation")
        acf_results[p] = {"lag1": acfs[0], "acfs": dict(zip(lags, acfs))}
    fig.suptitle("4A — Return Autocorrelation", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "4A_autocorrelation")

    # --- 4B: Z-score test ---
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
        for lv in [1, 2, -1, -2]:
            ax2.axhline(lv, color="gray", linestyle="--" if abs(lv)==1 else ":",
                        linewidth=0.7)
        ax2.axhline(0, color="black", linewidth=0.5)
        ax2.set_ylabel("Z-Score (20-tick)"); ax2.set_xlabel("Timestamp")

        fig.suptitle(f"4B — {p}: Mean Reversion Zones", fontsize=10, y=1.01)
        fig.tight_layout()
        savefig(fig, f"4B_zscore_{p}")

    for p in products:
        lag1 = acf_results[p]["lag1"]
        verdict = "MEAN REVERTING" if lag1 < -0.05 else ("TRENDING" if lag1 > 0.05 else "NEUTRAL")
        print(f"  {p:30s}  lag-1 autocorr = {lag1:.4f}  →  {verdict}")
    print()
    return acf_results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 5 — SIGNAL PREDICTIVENESS (MULTI-HORIZON)
# ═══════════════════════════════════════════════════════════════════════
def section5(products, feat_dfs):
    """Test which signals predict future returns at multiple horizons."""
    print("=" * 72)
    print("SECTION 5 — SIGNAL PREDICTIVENESS (MULTI-HORIZON)")
    print("=" * 72)
    signal_names = ["ret1", "z20", "micro_delta", "wall_delta", "mm_delta",
                    "imbalance", "spread_chg"]
    horizons = [1, 2, 5, 10, 20]
    signal_results = {}

    for p in products:
        df = feat_dfs[p]
        results = {}
        for s in signal_names:
            horizon_corrs = {}
            for h in horizons:
                fwd_col = f"fwd_ret_{h}"
                valid = df[[s, fwd_col]].dropna()
                if len(valid) < 30:
                    horizon_corrs[h] = 0
                    continue
                corr = valid[s].corr(valid[fwd_col])
                horizon_corrs[h] = corr if not np.isnan(corr) else 0
            # Hit rate at h=1
            valid1 = df[[s, "fwd_ret_1"]].dropna()
            hit = 0.5
            if len(valid1) > 30:
                hit = ((np.sign(valid1[s]) == np.sign(valid1["fwd_ret_1"])) &
                       (valid1[s] != 0) & (valid1["fwd_ret_1"] != 0)).mean()
            results[s] = {"corrs": horizon_corrs, "hit": hit,
                          "corr": horizon_corrs.get(1, 0)}
        signal_results[p] = results

    # --- 5A: Signal correlation at h=1 ---
    for p in products:
        fig, ax = plt.subplots(figsize=(10, 5))
        res = signal_results[p]
        sorted_sigs = sorted(signal_names, key=lambda s: abs(res[s]["corr"]))
        corrs = [res[s]["corr"] for s in sorted_sigs]
        colors = ["#d62728" if c < 0 else "#1f77b4" for c in corrs]
        ax.barh(range(len(sorted_sigs)), corrs, color=colors, edgecolor="white", alpha=0.8)
        ax.set_yticks(range(len(sorted_sigs))); ax.set_yticklabels(sorted_sigs)
        ax.axvline(0, color="black", linewidth=0.5)
        ax.set_xlabel("Correlation with next-tick return")
        ax.set_title(f"{p} — Signal strength at horizon=1", fontsize=9)
        fig.tight_layout()
        savefig(fig, f"5A_signal_corr_{p}")

    # --- 5B: Signal decay across horizons ---
    for p in products:
        fig, ax = plt.subplots(figsize=(12, 6))
        res = signal_results[p]
        for s in signal_names:
            decay = [res[s]["corrs"].get(h, 0) for h in horizons]
            ax.plot(horizons, [abs(d) for d in decay], marker="o", linewidth=1.5,
                    markersize=4, label=s, alpha=0.8)
        ax.set_xlabel("Forward horizon (ticks)")
        ax.set_ylabel("|Correlation|")
        ax.set_title(f"{p} — Signal decay: which signals persist?", fontsize=9)
        ax.legend(fontsize=7, ncol=2)
        ax.set_xticks(horizons)
        fig.tight_layout()
        savefig(fig, f"5B_signal_decay_{p}")

    # --- 5C: Hit rate comparison ---
    fig, axes = plt.subplots(1, len(products), figsize=(7 * len(products), 5), squeeze=False)
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
        ax.set_title(f"{p} — Directional accuracy (h=1)", fontsize=9)
        ax.legend(fontsize=7)
    fig.suptitle("5C — Hit Rate Comparison", fontsize=12, y=1.02)
    fig.tight_layout()
    savefig(fig, "5C_hit_rate")

    for p in products:
        print(f"\n  {p}:")
        print(f"    {'Signal':15s} {'Corr(h1)':>8s} {'Corr(h5)':>8s} {'Corr(h20)':>9s} {'Hit':>7s}  Verdict")
        print(f"    {'-'*65}")
        res = signal_results[p]
        for s in sorted(signal_names, key=lambda s: abs(res[s]["corr"]), reverse=True):
            r = res[s]
            direction = "momentum" if r["corr"] > 0 else "contrarian"
            c5 = r["corrs"].get(5, 0); c20 = r["corrs"].get(20, 0)
            print(f"    {s:15s} {r['corr']:>8.4f} {c5:>8.4f} {c20:>9.4f} {r['hit']:>6.1%}  "
                  f"{'USE' if abs(r['corr']) > 0.02 else 'skip'} ({direction})")
    print()
    return signal_results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 6 — COUNTERPARTY & BOT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════
def section6(products, feat_dfs, trade_dfs):
    """Analyze trade patterns for bot detection.
    Note: In Prosperity 4 Round 1, buyer/seller IDs are EMPTY in sample data.
    In Prosperity 3, counterparty analysis (especially 'Olivia' detection) was the
    #1 alpha source. When IDs become available in later rounds or live data,
    the trader ID analysis below will activate automatically."""
    print("=" * 72)
    print("SECTION 6 — TRADE PATTERN & BOT ANALYSIS")
    print("=" * 72)

    for p in products:
        df = feat_dfs[p]
        if p not in trade_dfs or len(trade_dfs[p]) == 0:
            print(f"  {p}: No trade data available, skipping.")
            continue
        tdf = trade_dfs[p].copy()

        # Merge fair value onto trades
        wall_mid_series = df.set_index("timestamp")["wall_mid"]
        mid_series = df.set_index("timestamp")["mid_price"]

        def lookup_ts(series, t):
            idx = series.index.searchsorted(t, side="right") - 1
            return series.iloc[idx] if idx >= 0 else np.nan

        tdf["wall_mid"] = tdf["timestamp"].map(lambda t: lookup_ts(wall_mid_series, t))
        tdf["mid_at_trade"] = tdf["timestamp"].map(lambda t: lookup_ts(mid_series, t))

        # --- 6A: Trader ID analysis (only if IDs are present) ---
        has_buyer = "buyer" in tdf.columns
        has_seller = "seller" in tdf.columns
        all_traders = set()
        if has_buyer:
            all_traders.update(tdf["buyer"].dropna().unique())
        if has_seller:
            all_traders.update(tdf["seller"].dropna().unique())
        all_traders.discard("")

        if len(all_traders) > 0:
            print(f"\n  {p} — Trader IDs found: {sorted(all_traders)}")
            trader_stats = []
            for trader in sorted(all_traders):
                buys = tdf[tdf.get("buyer", pd.Series()) == trader] if has_buyer else pd.DataFrame()
                sells = tdf[tdf.get("seller", pd.Series()) == trader] if has_seller else pd.DataFrame()

                def avg_fwd_ret(subset):
                    rets = []
                    for _, trade in subset.iterrows():
                        t = trade["timestamp"]
                        fi = df["timestamp"].searchsorted(t)
                        if fi + 5 < len(df):
                            rets.append(df["mid_price"].iloc[fi + 5] - df["mid_price"].iloc[fi])
                    return np.mean(rets) if rets else 0

                arb, ars = avg_fwd_ret(buys), avg_fwd_ret(sells)
                trader_stats.append({
                    "trader": trader, "buys": len(buys), "sells": len(sells),
                    "total": len(buys) + len(sells), "ret_buy": arb, "ret_sell": ars,
                    "edge": arb - ars
                })
            trader_df = pd.DataFrame(trader_stats).sort_values("total", ascending=False)

            print(f"    {'Trader':20s} {'Buys':>6s} {'Sells':>6s} {'Total':>6s} "
                  f"{'Ret(Buy)':>9s} {'Ret(Sell)':>10s} {'Edge':>7s}  Flag")
            print(f"    {'-'*80}")
            for _, row in trader_df.iterrows():
                flag = "*** INFORMED ***" if abs(row["edge"]) > 1.0 and row["total"] > 10 else \
                       ("* likely *" if abs(row["edge"]) > 0.5 and row["total"] > 10 else "")
                print(f"    {row['trader']:20s} {row['buys']:>6d} {row['sells']:>6d} "
                      f"{row['total']:>6d} {row['ret_buy']:>9.3f} "
                      f"{row['ret_sell']:>10.3f} {row['edge']:>7.3f}  {flag}")

            fig, ax = plt.subplots(figsize=(12, 6))
            top = trader_df.head(10); y = range(len(top))
            ax.barh(y, top["buys"], height=0.4, color="green", alpha=0.7, label="Buys")
            ax.barh([yi + 0.4 for yi in y], top["sells"], height=0.4,
                    color="red", alpha=0.7, label="Sells")
            ax.set_yticks([yi + 0.2 for yi in y])
            ax.set_yticklabels(top["trader"], fontsize=8)
            ax.set_xlabel("Trade Count")
            ax.set_title(f"{p} — Trader Activity", fontsize=9); ax.legend()
            fig.tight_layout(); savefig(fig, f"6A_trader_activity_{p}")

            fig, ax = plt.subplots(figsize=(10, 5))
            active = trader_df[trader_df["total"] > 5]
            if len(active) > 0:
                colors = ["#d62728" if e > 0 else "#1f77b4" for e in active["edge"]]
                ax.barh(range(len(active)), active["edge"],
                        color=colors, edgecolor="white", alpha=0.8)
                ax.set_yticks(range(len(active)))
                ax.set_yticklabels(active["trader"], fontsize=8)
                ax.axvline(0, color="black", linewidth=0.5)
                ax.set_xlabel("Edge (ret after buy − ret after sell)")
                ax.set_title(f"{p} — Trader informativeness", fontsize=9)
            fig.tight_layout(); savefig(fig, f"6B_trader_edge_{p}")
        else:
            print(f"\n  {p} — No trader IDs in data (anonymised). "
                  f"Watch for IDs in live/later rounds.")

        # --- 6C: Trade prices vs fair value ---
        fig, ax = plt.subplots(figsize=(14, 6))
        spread_mean = df["spread"].mean()
        colors = np.where(tdf["price"] > tdf["wall_mid"] + spread_mean, "orange",
                 np.where(tdf["price"] < tdf["wall_mid"] - spread_mean, "red", "green"))
        ax.scatter(tdf["timestamp"], tdf["price"], c=colors, s=15, alpha=0.6,
                   edgecolors="none")
        ax.plot(df["timestamp"], df["wall_mid"], color="black", linewidth=0.8,
                alpha=0.6, label="Wall Mid")
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='green', label='Near FV'),
                           Patch(facecolor='orange', label='Overbidding'),
                           Patch(facecolor='red', label='Underselling'),
                           plt.Line2D([0], [0], color='black', label='Wall Mid')]
        ax.legend(handles=legend_elements, fontsize=7)
        ax.set_title(f"{p} — Trade prices vs fair value: colored dots = exploitable", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Trade Price")
        fig.tight_layout()
        savefig(fig, f"6C_trade_vs_fv_{p}")

        # --- 6D: Trade size fingerprinting ---
        fig, ax = plt.subplots(figsize=(10, 5))
        qtys = tdf["quantity"].dropna()
        ax.hist(qtys, bins=max(10, int(qtys.max() - qtys.min() + 1)),
                color="#5599dd", edgecolor="white", alpha=0.8)
        top_sizes = qtys.value_counts().head(5)
        for sz, cnt in top_sizes.items():
            ax.annotate(f"qty={sz} (n={cnt})", xy=(sz, cnt),
                        fontsize=7, ha="center", va="bottom",
                        bbox=dict(boxstyle="round,pad=0.2", fc="lightyellow", ec="orange"))
        ax.set_title(f"{p} — Trade size distribution: recurring sizes = bot orders", fontsize=9)
        ax.set_xlabel("Quantity"); ax.set_ylabel("Frequency")
        fig.tight_layout()
        savefig(fig, f"6D_trade_sizes_{p}")

        # --- 6E: Buyer vs seller pressure ---
        fig, ax = plt.subplots(figsize=(12, 5))
        tdf_valid = tdf.dropna(subset=["mid_at_trade"]).copy()
        tdf_valid["buyer_init"] = tdf_valid["price"] >= tdf_valid["mid_at_trade"]
        bins = np.arange(0, tdf["timestamp"].max() + 5000, 5000)
        bin_idx = np.clip(np.digitize(tdf_valid["timestamp"], bins) - 1, 0, len(bins) - 2)
        tdf_valid["bin"] = bin_idx
        buy_counts = tdf_valid.groupby("bin")["buyer_init"].sum()
        sell_counts = tdf_valid.groupby("bin")["buyer_init"].apply(lambda x: (~x).sum())
        bin_centers = (bins[:-1] + bins[1:]) / 2
        all_bins = range(len(bins) - 1)
        bc = [buy_counts.get(b, 0) for b in all_bins]
        sc = [sell_counts.get(b, 0) for b in all_bins]
        ax.bar(bin_centers, bc, width=4500, color="green", alpha=0.7, label="Buyer-initiated")
        ax.bar(bin_centers, sc, width=4500, bottom=bc, color="red", alpha=0.7, label="Seller-initiated")
        ax.set_title(f"{p} — Trade direction: persistent imbalance = directional signal", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Trade Count")
        ax.legend(fontsize=7)
        fig.tight_layout()
        savefig(fig, f"6E_trade_direction_{p}")

        # Print summary
        buyer_ratio = tdf_valid["buyer_init"].mean() if len(tdf_valid) > 0 else 0.5
        top_sizes_str = ", ".join([f"{sz}(n={cnt})" for sz, cnt in
                                   qtys.value_counts().head(3).items()])
        print(f"\n  {p:30s}  trades={len(tdf)}  top_sizes=[{top_sizes_str}]  "
              f"buyer_ratio={buyer_ratio:.1%}")
    print()


# ═══════════════════════════════════════════════════════════════════════
# SECTION 7 — INTRADAY PATTERN DETECTION
# ═══════════════════════════════════════════════════════════════════════
def section7(products, feat_dfs):
    """Detect daily cycles and hidden patterns.
    Critical for ASH_COATED_OSMIUM which has a 'hidden pattern' per Round 1 hints."""
    print("=" * 72)
    print("SECTION 7 — INTRADAY PATTERN DETECTION")
    print("=" * 72)

    for p in products:
        df = feat_dfs[p]
        days = sorted(df["day"].unique())

        # --- 7A: All days overlaid on same x-axis (timestamp within day) ---
        fig, ax = plt.subplots(figsize=(14, 6))
        for di, day in enumerate(days):
            dd = df[df["day"] == day].copy()
            # Normalize price to start at 0 to reveal shape
            dd_price = dd["mid_price"].values - dd["mid_price"].values[0]
            ax.plot(dd["timestamp"].values, dd_price,
                    color=DAY_COLORS[di % len(DAY_COLORS)],
                    alpha=0.7, linewidth=0.8, label=f"Day {day}")
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_title(f"{p} — Price change from day open: do days share a pattern?", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Price − Day Open")
        ax.legend(fontsize=7)
        fig.tight_layout()
        savefig(fig, f"7A_intraday_overlay_{p}")

        # --- 7B: Average intraday path ---
        # Bin timestamps into intraday bins and compute average price path
        fig, ax = plt.subplots(figsize=(14, 6))
        all_day_paths = []
        max_ts = df["timestamp"].max()
        n_bins = 100
        for day in days:
            dd = df[df["day"] == day].copy()
            if len(dd) < 10:
                continue
            ts = dd["timestamp"].values
            prices = dd["mid_price"].values - dd["mid_price"].values[0]
            # Resample to uniform bins
            bin_edges = np.linspace(ts.min(), ts.max(), n_bins + 1)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            binned = np.digitize(ts, bin_edges) - 1
            binned = np.clip(binned, 0, n_bins - 1)
            bin_means = np.array([prices[binned == b].mean() if (binned == b).any()
                                  else np.nan for b in range(n_bins)])
            all_day_paths.append(bin_means)
            ax.plot(np.linspace(0, 1, n_bins), bin_means,
                    color=DAY_COLORS[di % len(DAY_COLORS)],
                    alpha=0.3, linewidth=0.5)

        if len(all_day_paths) > 1:
            avg_path = np.nanmean(all_day_paths, axis=0)
            std_path = np.nanstd(all_day_paths, axis=0)
            x = np.linspace(0, 1, n_bins)
            ax.plot(x, avg_path, color="black", linewidth=2.5, label="Average path")
            ax.fill_between(x, avg_path - std_path, avg_path + std_path,
                            alpha=0.2, color="gray", label="±1σ")
        ax.axhline(0, color="red", linewidth=0.5, linestyle="--")
        ax.set_title(f"{p} — Average intraday price path (0=open, 1=close)", fontsize=9)
        ax.set_xlabel("Fraction of trading day"); ax.set_ylabel("Price change from open")
        ax.legend(fontsize=7)
        fig.tight_layout()
        savefig(fig, f"7B_avg_intraday_path_{p}")

        # --- 7C: Autocorrelation at longer lags (periodicity detection) ---
        fig, ax = plt.subplots(figsize=(12, 5))
        rets = df["ret"].dropna()
        long_lags = list(range(1, min(201, len(rets) // 5)))
        acfs = [rets.autocorr(lag=l) for l in long_lags]
        ax.plot(long_lags, acfs, alpha=0.7, linewidth=0.8, color="#1f77b4")
        ax.axhline(0, color="black", linewidth=0.5)
        # Highlight significant peaks
        sig_threshold = 2 / np.sqrt(len(rets))
        ax.axhline(sig_threshold, color="red", linestyle=":", linewidth=0.8,
                   label=f"Significance ±{sig_threshold:.4f}")
        ax.axhline(-sig_threshold, color="red", linestyle=":", linewidth=0.8)
        # Find peaks
        acfs_arr = np.array(acfs)
        peaks = []
        for i in range(1, len(acfs_arr) - 1):
            if (abs(acfs_arr[i]) > sig_threshold and
                abs(acfs_arr[i]) > abs(acfs_arr[i-1]) and
                abs(acfs_arr[i]) > abs(acfs_arr[i+1])):
                peaks.append((long_lags[i], acfs_arr[i]))
        for lag, val in peaks[:5]:
            ax.annotate(f"lag={lag}", xy=(lag, val), fontsize=7,
                        ha="center", va="bottom" if val > 0 else "top",
                        bbox=dict(boxstyle="round,pad=0.2", fc="lightyellow", ec="orange"))
        ax.set_title(f"{p} — Long-lag autocorrelation: peaks reveal periodicity", fontsize=9)
        ax.set_xlabel("Lag"); ax.set_ylabel("Autocorrelation")
        ax.legend(fontsize=7)
        fig.tight_layout()
        savefig(fig, f"7C_periodicity_{p}")

        # Summary
        if peaks:
            peak_str = ", ".join([f"lag={l}(acf={v:.4f})" for l, v in peaks[:5]])
            print(f"  {p:30s}  Significant periodicities: {peak_str}")
        else:
            print(f"  {p:30s}  No significant periodicity detected")
    print()


# ═══════════════════════════════════════════════════════════════════════
# SECTION 8 — SPIKE DETECTION & EVENT STUDY
# ═══════════════════════════════════════════════════════════════════════
def section8(products, feat_dfs):
    """Detect price spikes and test if they revert (tradeable)."""
    print("=" * 72)
    print("SECTION 8 — SPIKE DETECTION & EVENT STUDY")
    print("=" * 72)
    spike_results = {}

    for p in products:
        df = feat_dfs[p]

        # --- 8A: Spike detection overlay ---
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        ax1.plot(df["timestamp"], df["mid_price"], alpha=0.7, linewidth=0.5,
                 color="#1f77b4", label="Mid Price")
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
        fig.suptitle(f"8A — {p}: Spike Detection ({n_spikes} spikes in {len(df)} ticks)",
                     fontsize=10, y=1.01)
        fig.tight_layout()
        savefig(fig, f"8A_spikes_{p}")

        # --- 8B: Post-spike event study ---
        fig, ax = plt.subplots(figsize=(12, 6))
        horizon = 20
        for label, indices, color in [("After UP spike", up_spikes.index.tolist(), "red"),
                                       ("After DOWN spike", dn_spikes.index.tolist(), "green")]:
            paths = []
            for i in indices:
                if i + horizon < len(df):
                    future = df["mid_price"].iloc[i:i + horizon + 1].values
                    paths.append(future - future[0])
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
        ax.set_title(f"{p} — Post-spike price path: slope toward 0 = reversion confirmed",
                     fontsize=9)
        ax.legend(fontsize=8)
        fig.tight_layout()
        savefig(fig, f"8B_spike_reversion_{p}")

        # Stats
        up_idx = up_spikes.index.tolist()
        dn_idx = dn_spikes.index.tolist()
        avg_rev_up = np.mean([df["mid_price"].iloc[i + 5] - df["mid_price"].iloc[i]
                              for i in up_idx if i + 5 < len(df)]) if up_idx else 0
        avg_rev_dn = np.mean([df["mid_price"].iloc[i + 5] - df["mid_price"].iloc[i]
                              for i in dn_idx if i + 5 < len(df)]) if dn_idx else 0
        reversion_ok = (avg_rev_up < 0 and len(up_idx) > 5) or \
                       (avg_rev_dn > 0 and len(dn_idx) > 5)
        spike_results[p] = {
            "n_spikes": n_spikes,
            "freq_per_10k": n_spikes / max(1, len(df)) * 10000,
            "avg_mag": df.loc[df["spike"], "ret"].abs().mean() if n_spikes > 0 else 0,
            "reversion": reversion_ok,
        }
        verdict = "YES — reversion confirmed" if reversion_ok else "NO — insufficient evidence"
        print(f"  {p:30s}  spikes/10k={spike_results[p]['freq_per_10k']:.1f}  "
              f"avg_rev_up_5={avg_rev_up:.3f}  avg_rev_dn_5={avg_rev_dn:.3f}  →  {verdict}")
    print()
    return spike_results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 9 — CROSS-PRODUCT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════
def section9(products, feat_dfs):
    """Check if products are correlated or have lead-lag relationships."""
    print("=" * 72)
    print("SECTION 9 — CROSS-PRODUCT ANALYSIS")
    print("=" * 72)

    if len(products) < 2:
        print("  Only one product — skipping.\n")
        return {}

    # Build aligned return matrix
    ret_dict = {}
    for p in products:
        df = feat_dfs[p]
        s = df.set_index(["day", "timestamp"])["mid_price"]
        ret_dict[p] = s

    aligned = pd.DataFrame(ret_dict).dropna()
    rets = aligned.diff().dropna()

    # --- 9A: Normalized price overlay ---
    fig, ax = plt.subplots(figsize=(14, 6))
    for idx, p in enumerate(products):
        normed = (aligned[p] - aligned[p].mean()) / aligned[p].std()
        ax.plot(normed.values, alpha=0.7, linewidth=0.6,
                color=DAY_COLORS[idx % len(DAY_COLORS)], label=p)
    ax.set_title("9A — Do products move together? (overlapping = correlated)", fontsize=10)
    ax.set_xlabel("Tick Index"); ax.set_ylabel("Z-scored Price")
    ax.legend()
    fig.tight_layout()
    savefig(fig, "9A_normalised_prices")

    # --- 9B: Correlation matrix ---
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
    ax.set_title("9B — Return correlation matrix", fontsize=10)
    fig.tight_layout()
    savefig(fig, "9B_correlation_matrix")

    # --- 9C: Lead-lag ---
    pairs = list(itertools.combinations(products, 2))
    if pairs:
        fig, axes = plt.subplots(1, len(pairs), figsize=(10 * len(pairs), 5), squeeze=False)
        lag_range = range(-10, 11)
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
            ax.set_title(f"{p1} vs {p2}: Lead-lag", fontsize=9)
        fig.tight_layout()
        savefig(fig, "9C_lead_lag")

    print("\n  Correlation matrix:")
    print(corr_mat.to_string(float_format=lambda x: f"{x:.4f}"))
    strong = [(p1, p2, corr_mat.loc[p1, p2]) for p1, p2 in pairs
              if abs(corr_mat.loc[p1, p2]) > 0.3]
    if strong:
        print(f"\n  Notable correlations: {strong}")
    else:
        print("\n  No notable correlations found.")
    print()
    return {"corr_mat": corr_mat}


# ═══════════════════════════════════════════════════════════════════════
# SECTION 10 — POSITION & INVENTORY RISK
# ═══════════════════════════════════════════════════════════════════════
def section10(products, feat_dfs, spread_results):
    """Simulate a take/clear/make strategy to assess position risk."""
    print("=" * 72)
    print("SECTION 10 — POSITION & INVENTORY RISK")
    print("=" * 72)
    pos_results = {}

    for p in products:
        df = feat_dfs[p]
        te = spread_results.get(p, {}).get("take_edge", 1.0)
        pe = spread_results.get(p, {}).get("passive_edge", 1.0)
        limit = POSITION_LIMITS.get(p, DEFAULT_LIMIT)

        # Take/clear/make simulation
        position = 0
        positions = []
        pnl = 0
        pnls = []
        fv = df["wall_mid"].values
        ask1 = df["ask_price_1"].values
        bid1 = df["bid_price_1"].values
        ask_v1 = df["ask_volume_1"].fillna(0).values
        bid_v1 = df["bid_volume_1"].fillna(0).values

        for i in range(len(df)):
            # 1) TAKE: sweep mispriced liquidity
            if ask1[i] < fv[i] - te and position < limit:
                qty = min(int(ask_v1[i]), limit - position, 10)
                position += qty
                pnl -= ask1[i] * qty

            if bid1[i] > fv[i] + te and position > -limit:
                qty = min(int(bid_v1[i]), limit + position, 10)
                position -= qty
                pnl += bid1[i] * qty

            # 2) CLEAR: reduce exposure near fair value
            if abs(position) > limit * 0.5:
                clear_qty = min(abs(position) - int(limit * 0.3), 3)
                if position > 0 and bid1[i] >= fv[i] - 1:
                    sq = min(clear_qty, position)
                    position -= sq
                    pnl += bid1[i] * sq
                elif position < 0 and ask1[i] <= fv[i] + 1:
                    sq = min(clear_qty, -position)
                    position += sq
                    pnl -= ask1[i] * sq

            # 3) MAKE: passive quotes (simulated fill at edge)
            # Skip for now — passive fills depend on bot behavior

            positions.append(position)
            pnls.append(pnl + position * fv[i])  # Mark-to-market

        positions = np.array(positions)
        pnls = np.array(pnls)

        # --- 10A: Position over time ---
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        ax1.plot(df["timestamp"], positions, alpha=0.7, linewidth=0.5, color="#1f77b4")
        ax1.axhline(limit, color="red", linestyle="--", linewidth=1, label=f"+{limit} limit")
        ax1.axhline(-limit, color="red", linestyle="--", linewidth=1, label=f"-{limit} limit")
        ax1.axhline(limit * 0.75, color="orange", linestyle=":", linewidth=0.8, label="75% warning")
        ax1.axhline(-limit * 0.75, color="orange", linestyle=":", linewidth=0.8)
        ax1.set_title(f"{p} — Simulated position (take_edge={te:.2f})", fontsize=9)
        ax1.set_ylabel("Position"); ax1.legend(fontsize=7)

        ax2.plot(df["timestamp"], pnls, alpha=0.7, linewidth=0.8, color="#2ca02c")
        ax2.set_title("Mark-to-market PnL", fontsize=9)
        ax2.set_xlabel("Timestamp"); ax2.set_ylabel("Cumulative PnL")
        fig.tight_layout()
        savefig(fig, f"10A_position_pnl_{p}")

        pct_at_limit = (np.abs(positions) >= limit * 0.9).mean() * 100
        final_pnl = pnls[-1] if len(pnls) > 0 else 0
        pos_results[p] = {
            "pct_at_limit": pct_at_limit,
            "final_pnl": final_pnl,
            "max_pos": int(np.max(np.abs(positions))),
        }
        print(f"  {p:30s}  %_at_limit={pct_at_limit:.1f}%  max_pos={pos_results[p]['max_pos']}  "
              f"final_mtm_pnl={final_pnl:.0f}")
    print()
    return pos_results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 11 — PARAMETER SENSITIVITY
# ═══════════════════════════════════════════════════════════════════════
def section11(products, feat_dfs):
    """Grid search over take_edge x passive_edge to find optimal parameters."""
    print("=" * 72)
    print("SECTION 11 — PARAMETER SENSITIVITY")
    print("=" * 72)

    for p in products:
        df = feat_dfs[p]
        limit = POSITION_LIMITS.get(p, DEFAULT_LIMIT)
        fv = df["wall_mid"].values
        ask1 = df["ask_price_1"].values
        bid1 = df["bid_price_1"].values
        ask_v1 = df["ask_volume_1"].fillna(0).values
        bid_v1 = df["bid_volume_1"].fillna(0).values

        te_range = np.arange(0.5, 6.1, 0.5)
        clear_thresholds = [0.3, 0.5, 0.7]
        results_grid = np.zeros((len(te_range), len(clear_thresholds)))

        for ti, te in enumerate(te_range):
            for ci, ct in enumerate(clear_thresholds):
                position = 0
                pnl = 0
                for i in range(len(df)):
                    if ask1[i] < fv[i] - te and position < limit:
                        qty = min(int(ask_v1[i]), limit - position, 10)
                        position += qty
                        pnl -= ask1[i] * qty
                    if bid1[i] > fv[i] + te and position > -limit:
                        qty = min(int(bid_v1[i]), limit + position, 10)
                        position -= qty
                        pnl += bid1[i] * qty
                    # Clear
                    if abs(position) > limit * ct:
                        cq = min(abs(position) - int(limit * 0.3), 3)
                        if position > 0 and bid1[i] >= fv[i] - 1:
                            sq = min(cq, position)
                            position -= sq
                            pnl += bid1[i] * sq
                        elif position < 0 and ask1[i] <= fv[i] + 1:
                            sq = min(cq, -position)
                            position += sq
                            pnl -= ask1[i] * sq
                mtm = pnl + position * fv[-1]
                results_grid[ti, ci] = mtm

        # --- 11A: Heatmap ---
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(results_grid, cmap="RdYlGn", aspect="auto",
                       origin="lower")
        ax.set_xticks(range(len(clear_thresholds)))
        ax.set_xticklabels([f"{ct:.0%}" for ct in clear_thresholds])
        ax.set_yticks(range(len(te_range)))
        ax.set_yticklabels([f"{te:.1f}" for te in te_range])
        ax.set_xlabel("Clear Threshold (% of limit)")
        ax.set_ylabel("Take Edge")
        for i in range(len(te_range)):
            for j in range(len(clear_thresholds)):
                ax.text(j, i, f"{results_grid[i, j]:.0f}", ha="center", va="center",
                        fontsize=7, color="black")
        plt.colorbar(im, ax=ax, shrink=0.8, label="MtM PnL")
        best_idx = np.unravel_index(results_grid.argmax(), results_grid.shape)
        ax.set_title(f"{p} — Parameter grid: best TE={te_range[best_idx[0]]:.1f}, "
                     f"CT={clear_thresholds[best_idx[1]]:.0%}", fontsize=9)
        fig.tight_layout()
        savefig(fig, f"11A_param_grid_{p}")

        best_te = te_range[best_idx[0]]
        best_ct = clear_thresholds[best_idx[1]]
        best_pnl = results_grid[best_idx]
        print(f"  {p:30s}  best_take_edge={best_te:.1f}  best_clear_thresh={best_ct:.0%}  "
              f"best_pnl={best_pnl:.0f}")
    print()


# ═══════════════════════════════════════════════════════════════════════
# SECTION 12 — STRATEGY DECISION DASHBOARD
# ═══════════════════════════════════════════════════════════════════════
def section12(products, feat_dfs, verdicts, fv_results, spread_results,
              acf_results, signal_results, spike_results, pos_results):
    """Consolidated dashboard per product with final recommendations."""
    print("=" * 72)
    print("SECTION 12 — STRATEGY DECISION DASHBOARD")
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
        te = sr.get("take_edge", 1)
        pe = sr.get("passive_edge", 1)

        fig, axes = plt.subplots(3, 3, figsize=(22, 18))

        # [0,0] Price history + mean
        ax = axes[0, 0]
        days = sorted(df["day"].unique())
        for di, day in enumerate(days):
            dd = df[df["day"] == day]
            ax.plot(dd["timestamp"], dd["mid_price"],
                    color=DAY_COLORS[di % len(DAY_COLORS)], alpha=0.7, linewidth=0.5)
        ax.axhline(df["mid_price"].mean(), color="black", linestyle="--", linewidth=1)
        ax.set_title(f"Price → {v}", fontsize=9)
        ax.set_xlabel("Timestamp"); ax.set_ylabel("Price")

        # [0,1] Autocorrelation
        ax = axes[0, 1]
        lags = [1, 2, 3, 5, 10]
        rets = df["ret"].dropna()
        acfs_vals = [rets.autocorr(lag=l) for l in lags]
        colors_a = ["#d62728" if a < 0 else "#1f77b4" for a in acfs_vals]
        ax.bar(range(len(lags)), acfs_vals, color=colors_a, edgecolor="white")
        ax.set_xticks(range(len(lags))); ax.set_xticklabels([str(l) for l in lags])
        ax.axhline(0, color="black", linewidth=0.5)
        mr = "MR" if acfs_vals[0] < -0.05 else ("TR" if acfs_vals[0] > 0.05 else "N")
        ax.set_title(f"ACF → {mr}", fontsize=9)

        # [0,2] Z-score
        ax = axes[0, 2]
        ax.plot(df["timestamp"], df["z20"], alpha=0.7, linewidth=0.5, color="#ff7f0e")
        for lv in [1, -1, 2, -2]:
            ax.axhline(lv, color="gray", linestyle="--" if abs(lv)==1 else ":",
                       linewidth=0.7)
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_title("Z-Score (20-tick)", fontsize=9)

        # [1,0] Spread distribution
        ax = axes[1, 0]
        sp = df["spread"].dropna()
        ax.hist(sp, bins=50, color="#5599dd", edgecolor="white", alpha=0.8)
        ax.axvline(sp.median(), color="orange", linestyle="--", linewidth=1)
        ax.set_title(f"Spread (TE={te:.2f}, PE={pe:.2f})", fontsize=9)

        # [1,1] Signal correlation
        ax = axes[1, 1]
        signal_names = ["ret1", "z20", "micro_delta", "wall_delta", "mm_delta",
                        "imbalance", "spread_chg"]
        if sig:
            sorted_sigs = sorted(signal_names, key=lambda s: abs(sig.get(s, {}).get("corr", 0)))
            corrs = [sig.get(s, {}).get("corr", 0) for s in sorted_sigs]
            colors_s = ["#d62728" if c < 0 else "#1f77b4" for c in corrs]
            ax.barh(range(len(sorted_sigs)), corrs, color=colors_s, edgecolor="white")
            ax.set_yticks(range(len(sorted_sigs)))
            ax.set_yticklabels(sorted_sigs, fontsize=7)
            best_sig = sorted_sigs[-1]
            ax.set_title(f"Signals → Best: {best_sig}", fontsize=9)
        ax.axvline(0, color="black", linewidth=0.5)

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
        ax.set_title(f"Spikes → Reversion: {spike_verdict}", fontsize=9)

        # [2,0] Wall mid and MM mid
        ax = axes[2, 0]
        step = max(1, len(df) // 2000)
        ds = df.iloc[::step]
        ax.plot(ds["timestamp"], ds["wall_mid"], color="green", linewidth=0.8,
                alpha=0.7, label="Wall mid")
        ax.plot(ds["timestamp"], ds["mm_mid"], color="red", linewidth=0.8,
                alpha=0.7, label="MM mid")
        best_fv = min(fv, key=fv.get).replace("_std", "") if fv else "wall_mid"
        ax.set_title(f"Fair Value → {best_fv}", fontsize=9)
        ax.legend(fontsize=6)

        # [2,1] Simulated position
        ax = axes[2, 1]
        # Quick re-sim
        position = 0; positions_d = []
        fv_arr = df["wall_mid"].values
        a1 = df["ask_price_1"].values; b1 = df["bid_price_1"].values
        av1 = df["ask_volume_1"].fillna(0).values; bv1 = df["bid_volume_1"].fillna(0).values
        limit = POSITION_LIMITS.get(p, DEFAULT_LIMIT)
        for i in range(len(df)):
            if a1[i] < fv_arr[i] - te and position < limit:
                position += min(int(av1[i]), limit - position, 5)
            if b1[i] > fv_arr[i] + te and position > -limit:
                position -= min(int(bv1[i]), limit + position, 5)
            positions_d.append(position)
        positions_d = np.array(positions_d)
        ax.plot(df["timestamp"], positions_d, alpha=0.7, linewidth=0.5, color="#1f77b4")
        ax.axhline(limit, color="red", linestyle="--", linewidth=0.8)
        ax.axhline(-limit, color="red", linestyle="--", linewidth=0.8)
        pct_lim = (np.abs(positions_d) >= limit * 0.9).mean() * 100
        ax.set_title(f"Position (at limit {pct_lim:.1f}%)", fontsize=9)

        # [2,2] FINAL RECOMMENDATION
        ax = axes[2, 2]
        ax.axis("off")
        if sig:
            best_signal = max(signal_names,
                              key=lambda s: abs(sig.get(s, {}).get("corr", 0)))
            best_corr = sig[best_signal]["corr"]
        else:
            best_signal = "N/A"; best_corr = 0

        rec_text = (
            f"{'━' * 40}\n"
            f"  FINAL RECOMMENDATION\n"
            f"{'━' * 40}\n\n"
            f"  Product type    : {v}\n"
            f"  Strategy        : {strat_map.get(v, 'MM')}\n"
            f"  Fair value      : {best_fv}\n"
            f"  Take edge       : {te:.2f}\n"
            f"  Passive edge    : {pe:.2f}\n"
            f"  Key signal      : {best_signal} ({best_corr:.3f})\n"
            f"  Spike reversion : {spike_verdict}\n"
            f"  Pos limit warn  : {limit * 0.75:.0f}\n"
        )
        ax.text(0.05, 0.95, rec_text, transform=ax.transAxes,
                fontsize=11, verticalalignment="top", fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.5", fc="#ffffdd", ec="#cc8800",
                          linewidth=2))

        fig.suptitle(f"{p} — Strategy Decision Dashboard", fontsize=14, y=1.01)
        fig.tight_layout()
        savefig(fig, f"12_dashboard_{p}")

        print(f"\n  ╔══════════════════════════════════════════════════════════╗")
        print(f"  ║  {p:^54s}  ║")
        print(f"  ╠══════════════════════════════════════════════════════════╣")
        print(f"  ║  Type            : {v:<36s}  ║")
        print(f"  ║  Strategy        : {strat_map.get(v, 'MM'):<36s}  ║")
        print(f"  ║  Fair Value      : {best_fv:<36s}  ║")
        print(f"  ║  Take Edge       : {te:<36.2f}  ║")
        print(f"  ║  Passive Edge    : {pe:<36.2f}  ║")
        print(f"  ║  Key Signal      : {best_signal + f' ({best_corr:.3f})':<36s}  ║")
        print(f"  ║  Spike Reversion : {spike_verdict:<36s}  ║")
        print(f"  ╚══════════════════════════════════════════════════════════╝")
    print()


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════
def main():
    print("\n" + "█" * 72)
    print("█  IMC PROSPERITY 4 — ROUND 1 MARKET ANALYSIS (V2)")
    print("█" * 72 + "\n")

    products, product_dfs, trade_dfs = load_data()
    feat_dfs = {p: compute_features(product_dfs[p]) for p in products}

    verdicts = section1(products, feat_dfs)
    fv_results = section2(products, feat_dfs)
    spread_results = section3(products, feat_dfs)
    acf_results = section4(products, feat_dfs)
    signal_results = section5(products, feat_dfs)
    section6(products, feat_dfs, trade_dfs)
    section7(products, feat_dfs)
    spike_results = section8(products, feat_dfs)
    section9(products, feat_dfs)
    pos_results = section10(products, feat_dfs, spread_results)
    section11(products, feat_dfs)
    section12(products, feat_dfs, verdicts, fv_results, spread_results,
              acf_results, signal_results, spike_results, pos_results)

    print(f"\n{'=' * 72}")
    print(f"ALL PLOTS SAVED TO: {PLOT_DIR}/")
    print(f"{'=' * 72}\n")


if __name__ == "__main__":
    main()
