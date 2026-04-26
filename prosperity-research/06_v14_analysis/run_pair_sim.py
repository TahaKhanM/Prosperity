"""Verify K5400 cheap, K5300 rich structural mispricing via simulation.

Strategy: K5400 buy + K5300 sell (vega-weighted).
Or simpler: just buy K5400 if mid < smile_fair - 1, sell K5400 if mid > smile_fair - 1
            (since structural cheapness means mean residual is -3 - we want to be biased long).
"""
import sys
import math
import json
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/scripts/round3_options")
from bs import bs_call_price, bs_call_vega, implied_vol_call

DATA_DIR = "/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets/round3"
TTE_DAYS = {0: 8, 1: 7, 2: 6}
strikes_all = [5000, 5100, 5200, 5300, 5400, 5500]


def compute_iv_grid(day: int):
    df = pd.read_csv(f"{DATA_DIR}/prices_round_3_day_{day}.csv", sep=";")
    vfe = df[df["product"] == "VELVETFRUIT_EXTRACT"].set_index("timestamp")["mid_price"]
    t_yr = TTE_DAYS[day] / 365.0
    iv_df = pd.DataFrame(index=vfe.index)
    iv_df["S"] = vfe
    book_df = {}
    for K in strikes_all:
        v = df[df["product"] == f"VEV_{K}"].set_index("timestamp")
        book_df[K] = v[["bid_price_1","bid_volume_1","ask_price_1","ask_volume_1","mid_price"]]
        v_aligned = v["mid_price"].reindex(vfe.index)
        ivs = []
        for s, p in zip(vfe.values, v_aligned.values):
            if math.isnan(p):
                ivs.append(np.nan)
                continue
            iv = implied_vol_call(float(p), float(s), float(K), t_yr)
            ivs.append(iv if iv is not None and not math.isnan(iv) else np.nan)
        iv_df[f"K{K}"] = ivs
    return df, iv_df, book_df, t_yr


def fit_smile_per_ts(iv_df: pd.DataFrame, exclude_K: int):
    """Return per-timestamp coefs of quadratic smile fit excluding `exclude_K`."""
    others = [k for k in strikes_all if k != exclude_K]
    common = iv_df.dropna().index
    S_arr = iv_df.loc[common, "S"].values
    iv_others = iv_df.loc[common, [f"K{k}" for k in others]].values
    n = len(common)
    x_others = np.log(np.array(others)[None, :] / S_arr[:, None])
    A = np.stack([np.ones_like(x_others), x_others, x_others**2], axis=2)
    coefs = np.zeros((n, 3))
    for i in range(n):
        c, *_ = np.linalg.lstsq(A[i], iv_others[i], rcond=None)
        coefs[i] = c
    return common, S_arr, coefs


def predict_iv(coefs, S, K):
    x = np.log(K / S)
    return coefs[:, 0] + coefs[:, 1] * x + coefs[:, 2] * x**2


def sim_strike(target_K: int, day: int, edge: float = 1.0, take_size: int = 4, limit: int = 300, post_size: int = 0):
    """Simulate per-strike trade strategy.

    take_size: aggressive take (cross spread).
    post_size: passive quote inside spread (for mm). 0 = take only.
    edge: required edge in seashells for taking.
    """
    df, iv_df, book_df, t_yr = compute_iv_grid(day)
    common, S_arr, coefs = fit_smile_per_ts(iv_df, exclude_K=target_K)
    book = book_df[target_K]
    common = pd.Index(common).intersection(book.index)
    common = sorted(common)
    n = len(common)
    if n == 0: return None
    S_idx = pd.Series(S_arr, index=iv_df.dropna().index)

    iv_target_full = predict_iv(coefs, S_arr, target_K)
    iv_target_series = pd.Series(iv_target_full, index=iv_df.dropna().index)

    pos = 0
    cash = 0.0
    trades_taken = 0
    trades_filled_passive = 0
    fills_at_quote = []
    for ts in common:
        S = S_idx.loc[ts]
        iv = iv_target_series.loc[ts]
        if iv <= 0 or np.isnan(iv): continue
        fair = bs_call_price(float(S), float(target_K), t_yr, float(iv))
        bid = book.loc[ts, "bid_price_1"]
        ask = book.loc[ts, "ask_price_1"]
        bv = int(book.loc[ts, "bid_volume_1"]) if not pd.isna(book.loc[ts, "bid_volume_1"]) else 0
        av = int(book.loc[ts, "ask_volume_1"]) if not pd.isna(book.loc[ts, "ask_volume_1"]) else 0
        # take
        if not pd.isna(ask) and ask <= fair - edge and pos < limit:
            qty = min(av, take_size, limit - pos)
            if qty > 0:
                pos += qty; cash -= qty * ask; trades_taken += 1
        if not pd.isna(bid) and bid >= fair + edge and pos > -limit:
            qty = min(bv, take_size, limit + pos)
            if qty > 0:
                pos -= qty; cash += qty * bid; trades_taken += 1
    last_mid = book.loc[common[-1], "mid_price"]
    return {
        "K": target_K, "day": day, "trades_taken": trades_taken,
        "pos_end": pos, "pnl": cash + pos * last_mid,
        "n_ticks": n,
    }


def sim_strike_with_smile_skew(target_K: int, day: int, structural_skew: float, edge: float = 1.0,
                                take_size: int = 4, limit: int = 300):
    """Use shifted fair = smile_fair + structural_skew (where structural_skew is the historical mean residual)."""
    df, iv_df, book_df, t_yr = compute_iv_grid(day)
    common, S_arr, coefs = fit_smile_per_ts(iv_df, exclude_K=target_K)
    book = book_df[target_K]
    common = pd.Index(common).intersection(book.index)
    common = sorted(common)
    n = len(common)
    if n == 0: return None
    S_idx = pd.Series(S_arr, index=iv_df.dropna().index)
    iv_target_full = predict_iv(coefs, S_arr, target_K)
    iv_target_series = pd.Series(iv_target_full, index=iv_df.dropna().index)

    pos = 0
    cash = 0.0
    trades = 0
    for ts in common:
        S = S_idx.loc[ts]
        iv = iv_target_series.loc[ts]
        if iv <= 0 or np.isnan(iv): continue
        fair = bs_call_price(float(S), float(target_K), t_yr, float(iv)) + structural_skew
        bid = book.loc[ts, "bid_price_1"]
        ask = book.loc[ts, "ask_price_1"]
        bv = int(book.loc[ts, "bid_volume_1"]) if not pd.isna(book.loc[ts, "bid_volume_1"]) else 0
        av = int(book.loc[ts, "ask_volume_1"]) if not pd.isna(book.loc[ts, "ask_volume_1"]) else 0
        if not pd.isna(ask) and ask <= fair - edge and pos < limit:
            qty = min(av, take_size, limit - pos)
            if qty > 0:
                pos += qty; cash -= qty * ask; trades += 1
        if not pd.isna(bid) and bid >= fair + edge and pos > -limit:
            qty = min(bv, take_size, limit + pos)
            if qty > 0:
                pos -= qty; cash += qty * bid; trades += 1
    last_mid = book.loc[common[-1], "mid_price"]
    return {
        "K": target_K, "day": day, "trades": trades,
        "pos_end": pos, "pnl": cash + pos * last_mid, "skew": structural_skew,
    }


def main():
    out_simple = []
    out_skewed = []
    print("=== Simple smile-MM (raw smile fair, edge=1.0) ===")
    for K in strikes_all:
        for day in (0, 1, 2):
            r = sim_strike(K, day, edge=1.0)
            if r:
                out_simple.append(r)
                print(f"  K={K} day={day}: pnl={r['pnl']:+8.0f} trades={r['trades_taken']:>4} pos_end={r['pos_end']:>+4}")

    # Skewed sim with structural prior. Use prior from OTHER days only (cross-validation).
    # We have K5300 ~ +2.5 rich, K5400 ~ -3.2 cheap, K5500 ~ +2.6 rich, K5000 ~ -0.6 mostly.
    # For each test day, prior = mean residual from the other 2 days
    print("\n=== Skew-aware MM (prior from other 2 days) ===")
    structural = {}  # {K: {day: mean_residual}}
    with open("/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_v14_analysis/extra_results.json") as f:
        per_strike = json.load(f)["per_strike"]
    for r in per_strike:
        structural.setdefault(r["K"], {})[r["day"]] = r["mean"]

    for K in strikes_all:
        for test_day in (0, 1, 2):
            other_days = [d for d in (0, 1, 2) if d != test_day]
            prior = np.mean([structural[K][d] for d in other_days])
            r = sim_strike_with_smile_skew(K, test_day, prior, edge=1.0)
            if r:
                out_skewed.append({**r, "prior": prior})
                print(f"  K={K} day={test_day} prior={prior:+5.2f}: pnl={r['pnl']:+8.0f} trades={r['trades']:>4} pos_end={r['pos_end']:>+4}")

    with open("/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_v14_analysis/sim_results.json", "w") as f:
        json.dump({"simple": out_simple, "skewed": out_skewed}, f, indent=2)
    print("\nWrote sim_results.json")

    # Aggregate by strike
    print("\n=== Aggregate by strike ===")
    print(f"{'K':>5} {'simple_total':>14} {'skewed_total':>14}")
    for K in strikes_all:
        s_total = sum(r["pnl"] for r in out_simple if r["K"] == K)
        sk_total = sum(r["pnl"] for r in out_skewed if r["K"] == K)
        print(f"{K:>5} {s_total:>+14.0f} {sk_total:>+14.0f}")


if __name__ == "__main__":
    main()
