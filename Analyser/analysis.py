"""
IMC Prosperity 4 – Market Data Analysis Tool
=============================================
Run from terminal:  python3 analysis.py
Plots are saved as PNG files in ./plots/

Drop new round CSVs (prices_round_*_day_*.csv / trades_round_*_day_*.csv)
into this folder and re-run — the loader picks them up automatically.
"""

import os
import glob
import warnings
import statistics

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # non-interactive backend for .py mode
import matplotlib.pyplot as plt
import matplotlib.cm as cm

warnings.filterwarnings("ignore")

# ── output directory for plots ──────────────────────────────────────────────
PLOTS_DIR = "plots"
os.makedirs(PLOTS_DIR, exist_ok=True)

NOTEBOOK_MODE = False          # set True inside notebook cells to show plots


def savefig(name: str):
    path = os.path.join(PLOTS_DIR, name)
    plt.savefig(path, dpi=120, bbox_inches="tight")
    print(f"  [saved] {path}")
    if NOTEBOOK_MODE:
        plt.show()
    plt.close()


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1 – DATA LOADING
# ════════════════════════════════════════════════════════════════════════════

def load_prices() -> pd.DataFrame:
    """
    Scan the current directory for all prices_round_*_day_*.csv files,
    load them, tag each row with the round/day it came from, and
    concatenate into a single dataframe.
    """
    files = sorted(glob.glob("prices_round_*_day_*.csv"))
    if not files:
        raise FileNotFoundError("No prices_round_*_day_*.csv files found.")

    frames = []
    for f in files:
        # extract round and day from filename
        parts = f.replace(".csv", "").split("_")
        # filename: prices_round_X_day_Y
        rnd  = int(parts[2])
        day  = int(parts[4])
        df   = pd.read_csv(f, sep=";")
        df["round"] = rnd
        df["day"]   = day
        # file-level 'day' column already exists in the CSV; keep it as-is
        # (it matches what we parsed) but add a composite sort key
        df["sort_key"] = rnd * 1000 + day   # allows multi-round ordering
        frames.append(df)
        print(f"  Loaded {f}  → {len(df):,} rows  (round={rnd}, day={day})")

    prices = pd.concat(frames, ignore_index=True)
    prices.sort_values(["sort_key", "timestamp", "product"], inplace=True)
    prices.reset_index(drop=True, inplace=True)
    return prices


def load_trades() -> pd.DataFrame:
    """
    Scan the current directory for all trades_round_*_day_*.csv files.
    Tag each row with round/day and concatenate.
    """
    files = sorted(glob.glob("trades_round_*_day_*.csv"))
    if not files:
        print("  WARNING: No trades_round_*_day_*.csv files found.")
        return pd.DataFrame()

    frames = []
    for f in files:
        parts = f.replace(".csv", "").split("_")
        rnd  = int(parts[2])
        day  = int(parts[4])
        df   = pd.read_csv(f, sep=";")
        df["round"] = rnd
        df["day"]   = day
        df["sort_key"] = rnd * 1000 + day
        frames.append(df)
        print(f"  Loaded {f}  → {len(df):,} rows  (round={rnd}, day={day})")

    trades = pd.concat(frames, ignore_index=True)
    trades.sort_values(["sort_key", "timestamp"], inplace=True)
    trades.reset_index(drop=True, inplace=True)
    return trades


def split_by_product(prices: pd.DataFrame) -> dict:
    """Return a dict mapping product name → subset dataframe."""
    products = {}
    for prod in sorted(prices["product"].unique()):
        products[prod] = prices[prices["product"] == prod].copy()
    return products


def print_summary(products: dict, trades: pd.DataFrame):
    """Print a human-readable summary table of loaded data."""
    print("\n" + "═" * 70)
    print("  SUMMARY: Loaded Data")
    print("═" * 70)
    header = f"{'Product':<14} {'Days':>6} {'Ticks':>8} {'Price Min':>10} {'Price Max':>10} {'Mean Spread':>12}"
    print(header)
    print("─" * 70)
    for prod, df in products.items():
        days       = sorted(df["day"].unique())
        ticks      = len(df)
        pmin       = df["mid_price"].min()
        pmax       = df["mid_price"].max()
        spread     = (df["ask_price_1"] - df["bid_price_1"]).mean()
        days_str   = str(days)
        print(f"  {prod:<12} {days_str:>8} {ticks:>8,} {pmin:>10.2f} {pmax:>10.2f} {spread:>12.4f}")
    print("─" * 70)
    if not trades.empty:
        print(f"  Trade rows loaded: {len(trades):,}")
        print(f"  Symbols in trades: {sorted(trades['symbol'].unique())}")
    print("═" * 70 + "\n")


def section_1():
    print("\n" + "╔" + "═"*68 + "╗")
    print("║  SECTION 1: Data Loading" + " "*43 + "║")
    print("╚" + "═"*68 + "╝\n")
    prices = load_prices()
    trades = load_trades()
    products = split_by_product(prices)
    print_summary(products, trades)
    return prices, trades, products


# ════════════════════════════════════════════════════════════════════════════
# SECTION 2 – PRICE & FAIR VALUE ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

def compute_microprice(df: pd.DataFrame) -> pd.Series:
    """
    Microprice = volume-weighted mid using best bid/ask volumes.
    Formula: (bid_price_1 * ask_volume_1 + ask_price_1 * bid_volume_1)
             / (bid_volume_1 + ask_volume_1)
    Gives a more accurate fair value than the simple mid when one side
    has more size — it tilts the fair value toward the thinner side.
    """
    num = df["bid_price_1"] * df["ask_volume_1"] + df["ask_price_1"] * df["bid_volume_1"]
    den = df["bid_volume_1"] + df["ask_volume_1"]
    return num / den


def section_2(products: dict):
    print("\n" + "╔" + "═"*68 + "╗")
    print("║  SECTION 2: Price & Fair Value Analysis" + " "*28 + "║")
    print("╚" + "═"*68 + "╝\n")

    # colour palette for days
    day_colours = ["steelblue", "darkorange", "green", "red", "purple", "brown"]

    for prod, df in products.items():
        days = sorted(df["day"].unique())
        n_days = len(days)

        fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=False)
        fig.suptitle(f"{prod} – Price & Fair Value Analysis", fontsize=14, fontweight="bold")

        # ── panel 1: mid_price per day ───────────────────────────────────
        ax = axes[0]
        for i, day in enumerate(days):
            d = df[df["day"] == day]
            col = day_colours[i % len(day_colours)]
            ax.plot(d["timestamp"], d["mid_price"], color=col, lw=0.8,
                    label=f"Day {day}", alpha=0.9)
        ax.set_title("Mid Price (CSV column)")
        ax.set_ylabel("Price")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)

        # ── panel 2: simple mid vs microprice ───────────────────────────
        ax = axes[1]
        df2 = df[df["day"] == days[0]].copy()   # first day for clarity
        simple_mid  = (df2["bid_price_1"] + df2["ask_price_1"]) / 2
        micro       = compute_microprice(df2)
        ax.plot(df2["timestamp"], simple_mid, color="steelblue", lw=0.8,
                label="Simple Mid", alpha=0.8)
        ax.plot(df2["timestamp"], micro,      color="crimson",   lw=0.8,
                label="Microprice",  alpha=0.8)
        ax.set_title(f"Simple Mid vs Microprice – Day {days[0]}")
        ax.set_ylabel("Price")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)

        # ── panel 3: rolling means on all days ──────────────────────────
        ax = axes[2]
        for i, day in enumerate(days):
            d = df[df["day"] == day].copy()
            col = day_colours[i % len(day_colours)]
            ax.plot(d["timestamp"], d["mid_price"], color=col, lw=0.5, alpha=0.4)
            for w, ls in [(10, "-"), (20, "--"), (50, ":")]:
                rm = d["mid_price"].rolling(w).mean()
                ax.plot(d["timestamp"], rm, color=col, lw=1.2, ls=ls,
                        label=f"Day {day} RM{w}" if i == 0 else None)
        ax.set_title("Rolling Means (10 / 20 / 50 ticks)")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Price")
        ax.legend(loc="upper right", fontsize=7)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        savefig(f"s2_{prod.lower()}_price_analysis.png")

        # ── text summary ─────────────────────────────────────────────────
        mp = df["mid_price"]
        std = mp.std()
        drifting = "DRIFTING" if std > 5 else "STATIONARY"
        print(f"  {prod}:")
        print(f"    Mean mid-price : {mp.mean():.4f}")
        print(f"    Std dev        : {std:.4f}  → {drifting}")
        print(f"    Min            : {mp.min():.4f}")
        print(f"    Max            : {mp.max():.4f}")
        print()


# ════════════════════════════════════════════════════════════════════════════
# SECTION 3 – SPREAD ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

def section_3(products: dict):
    print("\n" + "╔" + "═"*68 + "╗")
    print("║  SECTION 3: Spread Analysis" + " "*40 + "║")
    print("╚" + "═"*68 + "╝\n")

    day_colours = ["steelblue", "darkorange", "green", "red", "purple", "brown"]

    for prod, df in products.items():
        days = sorted(df["day"].unique())

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle(f"{prod} – Spread Analysis", fontsize=14, fontweight="bold")

        # ── spread over time ─────────────────────────────────────────────
        ax = axes[0]
        for i, day in enumerate(days):
            d = df[df["day"] == day]
            spread = d["ask_price_1"] - d["bid_price_1"]
            ax.plot(d["timestamp"], spread, color=day_colours[i % len(day_colours)],
                    lw=0.7, label=f"Day {day}", alpha=0.85)
        ax.set_title("Bid-Ask Spread Over Time")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Spread (ticks)")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # ── spread histogram ─────────────────────────────────────────────
        ax = axes[1]
        spread_all = df["ask_price_1"] - df["bid_price_1"]
        ax.hist(spread_all, bins=40, color="steelblue", edgecolor="white", alpha=0.8)
        ax.axvline(spread_all.mean(), color="red", lw=1.5, ls="--",
                   label=f"Mean {spread_all.mean():.2f}")
        ax.set_title("Spread Distribution")
        ax.set_xlabel("Spread (ticks)")
        ax.set_ylabel("Frequency")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        savefig(f"s3_{prod.lower()}_spread_analysis.png")

        # ── text summary ─────────────────────────────────────────────────
        spread = df["ask_price_1"] - df["bid_price_1"]
        wide_threshold = spread.mean() + 2 * spread.std()
        narrow_threshold = spread.mean() - spread.std()
        wide_pct  = (spread > wide_threshold).mean() * 100
        narrow_pct = (spread < narrow_threshold).mean() * 100

        # theoretical max profit per round-trip (half spread each leg)
        round_trip_profit = spread.mean() / 2

        print(f"  {prod}:")
        print(f"    Mean spread    : {spread.mean():.4f}")
        print(f"    Median spread  : {float(np.median(spread)):.4f}")
        print(f"    Spread std     : {spread.std():.4f}")
        print(f"    Min spread     : {spread.min():.4f}")
        print(f"    Max spread     : {spread.max():.4f}")
        print(f"    Wide spread (>{wide_threshold:.1f}) frequency: {wide_pct:.2f}%")
        print(f"    Narrow spread (<{narrow_threshold:.1f}) frequency: {narrow_pct:.2f}%")
        print(f"    Theoretical max round-trip profit (½ spread): {round_trip_profit:.4f}")
        print()


# ════════════════════════════════════════════════════════════════════════════
# SECTION 4 – MEAN REVERSION TEST
# ════════════════════════════════════════════════════════════════════════════

def autocorr_at_lag(series: pd.Series, lag: int) -> float:
    """Pearson autocorrelation of a series at a given lag."""
    s = series.dropna()
    if len(s) <= lag:
        return float("nan")
    return float(np.corrcoef(s[lag:], s[:-lag])[0, 1])


def section_4(products: dict):
    print("\n" + "╔" + "═"*68 + "╗")
    print("║  SECTION 4: Mean Reversion Test" + " "*36 + "║")
    print("╚" + "═"*68 + "╝\n")

    LAGS = [1, 2, 3, 5, 10]

    for prod, df in products.items():
        days = sorted(df["day"].unique())

        # use first day for detailed plots
        d = df[df["day"] == days[0]].copy()
        d["ret"]    = d["mid_price"].diff()
        d["rm20"]   = d["mid_price"].rolling(20).mean()
        d["zscore"] = (d["mid_price"] - d["rm20"]) / d["mid_price"].rolling(20).std()

        # autocorrelation on all days' returns
        rets_all = df.groupby("day")["mid_price"].diff().dropna()
        ac = [autocorr_at_lag(rets_all, lag) for lag in LAGS]

        fig, axes = plt.subplots(1, 3, figsize=(16, 5))
        fig.suptitle(f"{prod} – Mean Reversion Analysis", fontsize=14, fontweight="bold")

        # z-score over time
        ax = axes[0]
        ax.plot(d["timestamp"], d["zscore"], color="steelblue", lw=0.7)
        ax.axhline(0,  color="black", lw=1)
        ax.axhline(2,  color="red",   lw=1, ls="--", label="±2σ")
        ax.axhline(-2, color="red",   lw=1, ls="--")
        ax.set_title("Z-Score of Mid Price (RM20)")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Z-Score")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # mid price + RM20
        ax = axes[1]
        ax.plot(d["timestamp"], d["mid_price"], color="steelblue", lw=0.7,
                label="Mid Price", alpha=0.7)
        ax.plot(d["timestamp"], d["rm20"],      color="red",       lw=1.2,
                label="RM20", alpha=0.9)
        ax.set_title(f"Mid Price vs 20-Tick Rolling Mean – Day {days[0]}")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Price")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # autocorrelation bar chart
        ax = axes[2]
        colours = ["red" if v < 0 else "steelblue" for v in ac]
        ax.bar([str(l) for l in LAGS], ac, color=colours, edgecolor="white", alpha=0.8)
        ax.axhline(0, color="black", lw=1)
        ax.set_title("Return Autocorrelation by Lag")
        ax.set_xlabel("Lag (ticks)")
        ax.set_ylabel("Correlation")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        savefig(f"s4_{prod.lower()}_mean_reversion.png")

        # ── verdict ────────────────────────────────────────────────────
        lag1 = ac[0]
        if lag1 < -0.05:
            verdict = "MEAN REVERTING"
        elif lag1 > 0.05:
            verdict = "TRENDING"
        else:
            verdict = "MIXED"

        print(f"  {prod}:")
        print(f"    Return autocorrelations → {dict(zip(LAGS, [f'{v:.4f}' for v in ac]))}")
        print(f"    Lag-1 autocorrelation   : {lag1:.4f}")
        print(f"    *** VERDICT: {verdict} ***")
        print()


# ════════════════════════════════════════════════════════════════════════════
# SECTION 5 – SIGNAL ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

def signal_stats(signal: pd.Series, next_ret: pd.Series, name: str) -> dict:
    """
    Compute correlation and directional hit-rate between a signal and
    the following tick's return.
    """
    mask = signal.notna() & next_ret.notna()
    s = signal[mask]
    r = next_ret[mask]
    if len(s) < 10:
        return {"name": name, "corr": float("nan"), "hit_rate": float("nan")}

    corr = float(np.corrcoef(s, r)[0, 1])
    # direction hit: sign(signal) == sign(next_ret)
    hits = ((np.sign(s) == np.sign(r)) & (r != 0)).sum()
    total = (r != 0).sum()
    hit_rate = hits / total if total > 0 else float("nan")
    return {"name": name, "corr": corr, "hit_rate": hit_rate}


def section_5(products: dict):
    print("\n" + "╔" + "═"*68 + "╗")
    print("║  SECTION 5: Signal Analysis" + " "*40 + "║")
    print("╚" + "═"*68 + "╝\n")

    for prod, df in products.items():
        days = sorted(df["day"].unique())
        d = df.copy()

        # ── feature engineering ──────────────────────────────────────────
        d["ret"]       = d["mid_price"].diff()
        d["rm20"]      = d["mid_price"].rolling(20).mean()
        d["z20"]       = d["mid_price"] - d["rm20"]
        d["micro"]     = compute_microprice(d)
        d["micro_delta"] = d["micro"] - d["mid_price"]
        d["next_ret"]  = d["ret"].shift(-1)

        # ── three signals ────────────────────────────────────────────────
        sig1 = signal_stats(d["ret"],         d["next_ret"], "ret1 (momentum/reversal)")
        sig2 = signal_stats(d["z20"],         d["next_ret"], "z20  (mean reversion)")
        sig3 = signal_stats(d["micro_delta"], d["next_ret"], "microprice delta")

        # ── plot signal scatter + correlation summary ────────────────────
        fig, axes = plt.subplots(1, 3, figsize=(16, 5))
        fig.suptitle(f"{prod} – Signal Analysis", fontsize=14, fontweight="bold")

        for ax, (sig_series, meta) in zip(axes, [
            (d["ret"],         sig1),
            (d["z20"],         sig2),
            (d["micro_delta"], sig3),
        ]):
            mask = sig_series.notna() & d["next_ret"].notna()
            xs = sig_series[mask].values
            ys = d["next_ret"][mask].values
            ax.scatter(xs, ys, s=2, alpha=0.3, color="steelblue")
            # best-fit line
            if len(xs) > 2:
                m, b = np.polyfit(xs, ys, 1)
                xr = np.linspace(xs.min(), xs.max(), 100)
                ax.plot(xr, m * xr + b, color="red", lw=1.5)
            ax.set_title(f"{meta['name']}\ncorr={meta['corr']:.4f}  hit%={meta['hit_rate']*100:.1f}%")
            ax.set_xlabel("Signal value")
            ax.set_ylabel("Next tick return")
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        savefig(f"s5_{prod.lower()}_signals.png")

        # ── print results & recommended weights ─────────────────────────
        print(f"  {prod}:")
        for s in [sig1, sig2, sig3]:
            corr = s["corr"]
            hr   = s["hit_rate"]
            if abs(corr) < 0.01:
                weight = "0  (no predictive power)"
            elif corr < 0:
                weight = f"{corr:.4f}  → use as CONTRARIAN / mean-reversion signal"
            else:
                weight = f"{corr:.4f}  → use as MOMENTUM signal"
            print(f"    {s['name']}")
            print(f"      Correlation  : {corr:.4f}")
            print(f"      Hit rate     : {hr*100:.2f}%")
            print(f"      Weight       : {weight}")
        print()


# ════════════════════════════════════════════════════════════════════════════
# SECTION 6 – ORDER BOOK DEPTH ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

def section_6(products: dict):
    print("\n" + "╔" + "═"*68 + "╗")
    print("║  SECTION 6: Order Book Depth Analysis" + " "*30 + "║")
    print("╚" + "═"*68 + "╝\n")

    day_colours = ["steelblue", "darkorange", "green", "red"]

    for prod, df in products.items():
        days = sorted(df["day"].unique())
        d0   = df[df["day"] == days[0]].copy()

        # aggregate volumes, filling NaN (missing levels) with 0
        vol_cols_bid = ["bid_volume_1", "bid_volume_2", "bid_volume_3"]
        vol_cols_ask = ["ask_volume_1", "ask_volume_2", "ask_volume_3"]
        d0[vol_cols_bid] = d0[vol_cols_bid].fillna(0)
        d0[vol_cols_ask] = d0[vol_cols_ask].fillna(0)

        d0["total_bid_vol"] = d0[vol_cols_bid].sum(axis=1)
        d0["total_ask_vol"] = d0[vol_cols_ask].sum(axis=1)
        d0["imbalance"]     = ((d0["total_bid_vol"] - d0["total_ask_vol"])
                               / (d0["total_bid_vol"] + d0["total_ask_vol"]))
        d0["next_ret"]      = d0["mid_price"].diff().shift(-1)

        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle(f"{prod} – Order Book Depth Analysis (Day {days[0]})",
                     fontsize=14, fontweight="bold")

        # total bid/ask volume over time
        ax = axes[0, 0]
        ax.plot(d0["timestamp"], d0["total_bid_vol"], color="green", lw=0.8,
                label="Total Bid Vol")
        ax.plot(d0["timestamp"], d0["total_ask_vol"], color="red",   lw=0.8,
                label="Total Ask Vol")
        ax.set_title("Total Bid vs Ask Volume")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Volume")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # book imbalance over time
        ax = axes[0, 1]
        ax.plot(d0["timestamp"], d0["imbalance"], color="steelblue", lw=0.6)
        ax.axhline(0, color="black", lw=1)
        ax.set_title("Book Imbalance  (+1 = all bids, -1 = all asks)")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Imbalance")
        ax.grid(True, alpha=0.3)

        # volume at each level (bids)
        ax = axes[1, 0]
        for lv, col in zip([1, 2, 3], ["steelblue", "darkorange", "green"]):
            c = f"bid_volume_{lv}"
            if c in d0.columns:
                ax.fill_between(d0["timestamp"], d0[c].fillna(0),
                                alpha=0.5, label=f"Bid L{lv}", color=col)
        ax.set_title("Bid Volume by Level")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Volume")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # volume at each level (asks)
        ax = axes[1, 1]
        for lv, col in zip([1, 2, 3], ["steelblue", "darkorange", "green"]):
            c = f"ask_volume_{lv}"
            if c in d0.columns:
                ax.fill_between(d0["timestamp"], d0[c].fillna(0),
                                alpha=0.5, label=f"Ask L{lv}", color=col)
        ax.set_title("Ask Volume by Level")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Volume")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        savefig(f"s6_{prod.lower()}_orderbook_depth.png")

        # ── predictive test for imbalance ────────────────────────────────
        res = signal_stats(d0["imbalance"], d0["next_ret"], "book imbalance")
        print(f"  {prod}:")
        print(f"    Book imbalance → next ret correlation : {res['corr']:.4f}")
        print(f"    Book imbalance directional hit rate   : {res['hit_rate']*100:.2f}%")
        print()


# ════════════════════════════════════════════════════════════════════════════
# SECTION 7 – MARKET TRADES ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

def section_7(trades: pd.DataFrame, products: dict):
    print("\n" + "╔" + "═"*68 + "╗")
    print("║  SECTION 7: Market Trades Analysis" + " "*33 + "║")
    print("╚" + "═"*68 + "╝\n")

    if trades.empty:
        print("  No trade data available – skipping section 7.\n")
        return

    # normalise column name for product/symbol
    sym_col = "symbol" if "symbol" in trades.columns else "product"

    for prod, price_df in products.items():
        t = trades[trades[sym_col] == prod].copy()
        if t.empty:
            print(f"  {prod}: no trades found.\n")
            continue

        days = sorted(price_df["day"].unique())
        # merge mid price onto trades for context
        # use nearest mid price by timestamp (same day)
        # simple approach: merge on day+timestamp
        mid_lookup = price_df[["day", "timestamp", "mid_price",
                                "bid_price_1", "ask_price_1"]].copy()

        # only work with the first available day that has both trades + prices
        for day in days:
            td = t[t["day"] == day].copy()
            md = mid_lookup[mid_lookup["day"] == day].copy()
            if len(td) > 0 and len(md) > 0:
                break
        else:
            print(f"  {prod}: no matching day with both trades and prices.\n")
            continue

        td = td.sort_values("timestamp")
        md = md.sort_values("timestamp")

        # merge-asof: snap each trade to the last known mid price
        td = pd.merge_asof(td, md[["timestamp","mid_price","bid_price_1","ask_price_1"]],
                           on="timestamp", direction="backward")

        # classify trade direction
        td["mid_dist"] = td["price"] - td["mid_price"]
        td["is_buy"]   = td["price"] >= td["mid_price"]  # buyer initiated if ≥ mid

        # trade frequency: bin into 1000-ts windows
        bins = range(int(td["timestamp"].min()), int(td["timestamp"].max()) + 1001, 1000)
        td["ts_bin"]  = pd.cut(td["timestamp"], bins=list(bins), labels=False)
        freq          = td.groupby("ts_bin").size()

        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle(f"{prod} – Market Trades Analysis (Day {day})",
                     fontsize=14, fontweight="bold")

        # trade prices vs mid price
        ax = axes[0, 0]
        ax.plot(md["timestamp"], md["mid_price"], color="steelblue",
                lw=0.8, label="Mid Price", alpha=0.7)
        buy_t  = td[td["is_buy"]]
        sell_t = td[~td["is_buy"]]
        ax.scatter(buy_t["timestamp"],  buy_t["price"],  color="green", s=12, zorder=3,
                   label="Buyer-initiated")
        ax.scatter(sell_t["timestamp"], sell_t["price"], color="red",   s=12, zorder=3,
                   label="Seller-initiated")
        ax.set_title("Trade Prices vs Mid Price")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Price")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # trade frequency
        ax = axes[0, 1]
        ax.bar(freq.index, freq.values, color="steelblue", alpha=0.8)
        ax.set_title("Trade Frequency (per 1000-ts bin)")
        ax.set_xlabel("Bin index")
        ax.set_ylabel("# Trades")
        ax.grid(True, alpha=0.3)

        # trade size distribution
        ax = axes[1, 0]
        if "quantity" in td.columns:
            td["quantity"] = pd.to_numeric(td["quantity"], errors="coerce")
            ax.hist(td["quantity"].dropna(), bins=20, color="darkorange",
                    edgecolor="white", alpha=0.8)
        ax.set_title("Trade Size Distribution")
        ax.set_xlabel("Quantity")
        ax.set_ylabel("Frequency")
        ax.grid(True, alpha=0.3)

        # late-day analysis: trade frequency before/after 140,000
        ax = axes[1, 1]
        early = td[td["timestamp"] <= 140_000]
        late  = td[td["timestamp"]  > 140_000]
        ax.bar(["Early (≤140k)", "Late (>140k)"], [len(early), len(late)],
               color=["steelblue", "darkorange"], alpha=0.8)
        ax.set_title("Early vs Late Session Trade Count")
        ax.set_ylabel("# Trades")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        savefig(f"s7_{prod.lower()}_trades_analysis.png")

        # ── text summary ─────────────────────────────────────────────────
        buy_pct  = len(buy_t)  / len(td) * 100
        sell_pct = len(sell_t) / len(td) * 100
        print(f"  {prod} (day {day}):")
        print(f"    Total trades     : {len(td)}")
        print(f"    Buyer-initiated  : {buy_pct:.1f}%")
        print(f"    Seller-initiated : {sell_pct:.1f}%")
        if "quantity" in td.columns:
            print(f"    Mean trade size  : {td['quantity'].mean():.2f}")
        print(f"    Early-session (≤140k)  : {len(early)} trades")
        print(f"    Late-session  (>140k)  : {len(late)} trades")
        late_ratio = len(late) / max(len(early), 1)
        if late_ratio > 1.2:
            print(f"    → Late session MORE active ({late_ratio:.2f}×). Late-hold strategy relevant.")
        elif late_ratio < 0.8:
            print(f"    → Late session LESS active ({late_ratio:.2f}×). Early action dominates.")
        else:
            print(f"    → Activity roughly even across session.")
        print()


# ════════════════════════════════════════════════════════════════════════════
# SECTION 8 – POSITION LIMIT STRESS TEST
# ════════════════════════════════════════════════════════════════════════════

def simulate_mm(price_df: pd.DataFrame, fair_value_func,
                take_edge: float = 2.0, pos_limit: int = 80) -> pd.Series:
    """
    Simulate a simple market-making strategy on the price dataframe.

    Rules:
    - If ask_price_1 <= fair_value - take_edge  → BUY (take the cheap ask)
    - If bid_price_1 >= fair_value + take_edge  → SELL (take the rich bid)
    - Trades assumed to fill at best quote volume (bid_volume_1 / ask_volume_1)
    - Position capped at ±pos_limit

    Returns a Series of simulated position over time.
    """
    positions = []
    pos = 0
    for _, row in price_df.iterrows():
        fv      = fair_value_func(row)
        bid1    = row["bid_price_1"]
        ask1    = row["ask_price_1"]
        bvol1   = row.get("bid_volume_1", 0) or 0
        avol1   = row.get("ask_volume_1", 0) or 0

        if ask1 <= fv - take_edge and pos < pos_limit:
            qty = min(int(avol1), pos_limit - pos)
            pos += qty
        elif bid1 >= fv + take_edge and pos > -pos_limit:
            qty = min(int(bvol1), pos_limit + pos)
            pos -= qty

        positions.append(pos)

    return pd.Series(positions, index=price_df.index)


def section_8(products: dict):
    print("\n" + "╔" + "═"*68 + "╗")
    print("║  SECTION 8: Position Limit Stress Test" + " "*29 + "║")
    print("╚" + "═"*68 + "╝\n")

    POS_LIMIT = 80

    fair_value_fns = {
        "EMERALDS": lambda row: 10_000.0,                         # fixed FV
        "TOMATOES": lambda row: row["mid_price"],                 # use current mid
    }

    for prod, df in products.items():
        days = sorted(df["day"].unique())
        fv_fn = fair_value_fns.get(prod, lambda row: row["mid_price"])

        fig, axes = plt.subplots(len(days), 1, figsize=(14, 5 * len(days)), squeeze=False)
        fig.suptitle(f"{prod} – Position Simulation (limit={POS_LIMIT})",
                     fontsize=14, fontweight="bold")

        for idx, day in enumerate(days):
            d   = df[df["day"] == day].copy()
            pos = simulate_mm(d, fv_fn, take_edge=2.0, pos_limit=POS_LIMIT)

            ax = axes[idx][0]
            ax.plot(d["timestamp"].values, pos.values, color="steelblue", lw=0.8)
            ax.axhline( POS_LIMIT, color="red",  lw=1.5, ls="--", label="+limit")
            ax.axhline(-POS_LIMIT, color="red",  lw=1.5, ls="--", label="-limit")
            ax.axhline(0,          color="black", lw=1)
            ax.set_title(f"Day {day}")
            ax.set_xlabel("Timestamp")
            ax.set_ylabel("Position")
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)

            # ── stats ────────────────────────────────────────────────────
            limit_hits = ((pos >= POS_LIMIT) | (pos <= -POS_LIMIT)).sum()
            limit_pct  = limit_hits / len(pos) * 100

            # average unwind time from max position
            at_limit   = (pos.abs() == POS_LIMIT)
            unwinds    = []
            i, n = 0, len(pos)
            while i < n:
                if at_limit.iloc[i]:
                    sign = np.sign(pos.iloc[i])
                    j = i + 1
                    while j < n and pos.iloc[j] * sign >= POS_LIMIT * 0.5:
                        j += 1
                    unwinds.append(j - i)
                    i = j
                else:
                    i += 1
            avg_unwind = statistics.mean(unwinds) if unwinds else float("nan")

            print(f"  {prod} – Day {day}:")
            print(f"    Position at limit   : {limit_pct:.2f}% of ticks")
            print(f"    Limit breach events : {limit_hits}")
            avg_str = f"{avg_unwind:.1f}" if not (isinstance(avg_unwind, float) and np.isnan(avg_unwind)) else "N/A"
            print(f"    Avg unwind (ticks)  : {avg_str}")
            if limit_pct > 10:
                print(f"    *** WARNING: high limit exposure – consider tightening take_edge "
                      f"or adding soft-cap logic ***")
            print()

        plt.tight_layout()
        savefig(f"s8_{prod.lower()}_position_sim.png")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 9 – PRODUCT CORRELATION
# ════════════════════════════════════════════════════════════════════════════

def section_9(products: dict):
    print("\n" + "╔" + "═"*68 + "╗")
    print("║  SECTION 9: Product Correlation" + " "*36 + "║")
    print("╚" + "═"*68 + "╝\n")

    prod_names = list(products.keys())
    if len(prod_names) < 2:
        print("  Need at least 2 products for correlation analysis.\n")
        return

    # use all available data; normalise each product's mid price
    series = {}
    for prod, df in products.items():
        grp = df.groupby("timestamp")["mid_price"].mean()
        series[prod] = grp

    # align on common timestamps
    aligned = pd.DataFrame(series).dropna()

    if aligned.empty:
        print("  No overlapping timestamps found.\n")
        return

    normed = (aligned - aligned.mean()) / aligned.std()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Product Correlation Analysis", fontsize=14, fontweight="bold")

    # normalised price chart
    ax = axes[0]
    colours = ["steelblue", "darkorange", "green", "red"]
    for i, prod in enumerate(aligned.columns):
        ax.plot(aligned.index, normed[prod], color=colours[i % len(colours)],
                lw=0.8, label=prod, alpha=0.8)
    ax.set_title("Normalised Mid Prices")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Z-Score")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # scatter of product 1 vs product 2
    ax = axes[1]
    p1, p2 = prod_names[0], prod_names[1]
    ax.scatter(aligned[p1], aligned[p2], s=3, alpha=0.3, color="steelblue")
    corr = aligned[p1].corr(aligned[p2])
    ax.set_title(f"Scatter {p1} vs {p2}  (r={corr:.4f})")
    ax.set_xlabel(p1)
    ax.set_ylabel(p2)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    savefig("s9_correlation.png")

    # lag correlation
    LAGS = [0, 1, 2, 3, 5, 10]
    rets1 = aligned[p1].pct_change().dropna()
    rets2 = aligned[p2].pct_change().dropna()

    print(f"  Contemporaneous correlation {p1} vs {p2}: {corr:.4f}")
    print(f"  Lag correlations (does {p1} LEAD {p2}):")
    for lag in LAGS:
        if lag == 0:
            lc = rets1.corr(rets2)
        else:
            lc = rets1.iloc[:-lag].corr(rets2.iloc[lag:])
        print(f"    Lag {lag:>2d}: {lc:.4f}")

    if abs(corr) > 0.7:
        verdict = f"CORRELATED (r={corr:.4f}) – one product may inform the other's FV."
    elif abs(corr) > 0.3:
        verdict = f"WEAKLY CORRELATED (r={corr:.4f}) – watch for regime changes."
    else:
        verdict = f"INDEPENDENT (r={corr:.4f}) – treat as separate products."

    print(f"\n  *** VERDICT: {verdict} ***\n")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 10 – STRATEGY RECOMMENDATION SUMMARY
# ════════════════════════════════════════════════════════════════════════════

def section_10(products: dict):
    print("\n" + "╔" + "═"*68 + "╗")
    print("║  SECTION 10: Strategy Recommendation Summary" + " "*23 + "║")
    print("╚" + "═"*68 + "╝\n")

    LAGS_AC = [1, 2, 3, 5, 10]

    rows = []

    for prod, df in products.items():
        mp   = df["mid_price"]
        std  = mp.std()

        # spread
        spread = (df["ask_price_1"] - df["bid_price_1"])
        mean_spread = spread.mean()

        # stationarity proxy: std relative to mean price
        cv = std / mp.mean()
        if cv < 0.001:
            prod_type = "STABLE"
            strategy  = "Fixed fair-value market maker"
            fv_method = f"Constant @ {mp.mean():.0f}"
            take_edge = max(1, round(mean_spread * 0.25))
            pass_edge = max(1, round(mean_spread * 0.40))
        elif cv < 0.01:
            prod_type = "DRIFTING"
            strategy  = "Rolling fair-value market maker"
            fv_method = "Rolling mean (20 ticks)"
            take_edge = max(1, round(mean_spread * 0.30))
            pass_edge = max(1, round(mean_spread * 0.45))
        else:
            prod_type = "VOLATILE"
            strategy  = "Mean-reversion or trend-following (needs further analysis)"
            fv_method = "Rolling mean (50 ticks) or external signal"
            take_edge = max(2, round(mean_spread * 0.35))
            pass_edge = max(2, round(mean_spread * 0.50))

        # lag-1 autocorrelation on returns
        rets = mp.diff().dropna()
        ac1  = autocorr_at_lag(rets, 1)

        # best signal (re-use logic from section 5)
        d2 = df.copy()
        d2["ret"]        = d2["mid_price"].diff()
        d2["rm20"]       = d2["mid_price"].rolling(20).mean()
        d2["z20"]        = d2["mid_price"] - d2["rm20"]
        d2["micro"]      = compute_microprice(d2)
        d2["micro_delta"] = d2["micro"] - d2["mid_price"]
        d2["next_ret"]   = d2["ret"].shift(-1)

        sigs = [
            signal_stats(d2["ret"],          d2["next_ret"], "ret1"),
            signal_stats(d2["z20"],          d2["next_ret"], "z20"),
            signal_stats(d2["micro_delta"],  d2["next_ret"], "microprice_delta"),
        ]
        best_sig = max(sigs, key=lambda s: abs(s["corr"]) if not np.isnan(s["corr"]) else 0)

        rows.append({
            "Product"        : prod,
            "Type"           : prod_type,
            "Strategy"       : strategy,
            "Fair Value"     : fv_method,
            "Take Edge"      : take_edge,
            "Passive Edge"   : pass_edge,
            "AC(lag=1)"      : f"{ac1:.4f}",
            "Best Signal"    : best_sig["name"],
            "Signal Corr"    : f"{best_sig['corr']:.4f}",
            "Mean Spread"    : f"{mean_spread:.4f}",
        })

    # ── print table ──────────────────────────────────────────────────────────
    col_order = ["Product", "Type", "Strategy", "Fair Value",
                 "Take Edge", "Passive Edge", "AC(lag=1)",
                 "Best Signal", "Signal Corr", "Mean Spread"]

    # column widths
    widths = {c: max(len(c), max(len(str(r[c])) for r in rows)) + 2 for c in col_order}

    header = "  " + "│".join(c.ljust(widths[c]) for c in col_order)
    sep    = "  " + "┼".join("─" * widths[c] for c in col_order)
    print(header)
    print(sep)
    for row in rows:
        line = "  " + "│".join(str(row[c]).ljust(widths[c]) for c in col_order)
        print(line)

    print("\n")
    print("  Key to columns:")
    print("    Take Edge    – how far from fair value to aggressively lift/hit")
    print("    Passive Edge – how far from fair value to post resting quotes")
    print("    AC(lag=1)    – return autocorrelation at lag 1 (<0 = mean-reverting)")
    print("    Best Signal  – highest |correlation| signal with next-tick direction")
    print()


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "█" * 70)
    print("  IMC Prosperity 4 – Market Analysis Tool")
    print("  Output plots → ./plots/")
    print("█" * 70 + "\n")

    # 1 – load
    prices, trades, products = section_1()

    # 2 – price / fair value
    section_2(products)

    # 3 – spread
    section_3(products)

    # 4 – mean reversion
    section_4(products)

    # 5 – signals
    section_5(products)

    # 6 – order book depth
    section_6(products)

    # 7 – market trades
    section_7(trades, products)

    # 8 – position stress test
    section_8(products)

    # 9 – correlation
    section_9(products)

    # 10 – summary
    section_10(products)

    print("\n" + "█" * 70)
    print("  Analysis complete.  Plots saved to ./plots/")
    print("█" * 70 + "\n")


if __name__ == "__main__":
    main()
