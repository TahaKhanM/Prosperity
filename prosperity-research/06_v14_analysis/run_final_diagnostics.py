"""Final additional diagnostics:
1. Per-product spread distribution (correctly using top-of-book).
2. HYDROGEL mean-reversion (one-tick lag autocorrelation profitability).
3. HYDROGEL "fade prior tick" simulation.
4. Volatility burst regimes (rolling z-score of |dx|).
5. Time-of-day binning of HYD vol and PnL.
6. K-residual time-series correlation (does d0 prior predict d2 residual?)
"""
import os
import json
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_DIR = "/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets/round3"
OUT_DIR = "/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_v14_analysis"
PLOT_DIR = os.path.join(OUT_DIR, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)


def correct_spread_diagnostics():
    """Use bid_price_1 / ask_price_1 (which IS top-of-book in this format).

    Findings:
    HYD spread = 16 typically with MM showing inside the book at level-1.
    Actually: bid_price_1 IS the highest bid (closer to mid), but the GAP between
    bid_1 and ask_1 is the inside spread. For HYD this is ~16 (hostile).
    """
    out = []
    for day in (0, 1, 2):
        df = pd.read_csv(f"{DATA_DIR}/prices_round_3_day_{day}.csv", sep=";")
        for prod in ["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT", "VEV_5000", "VEV_5100",
                     "VEV_5200", "VEV_5300", "VEV_5400", "VEV_5500"]:
            sub = df[df["product"] == prod]
            if len(sub) == 0: continue
            sp = (sub["ask_price_1"] - sub["bid_price_1"]).dropna()
            if len(sp) == 0: continue
            out.append({
                "day": day, "product": prod, "n": len(sp),
                "spread_min": int(sp.min()), "spread_med": float(sp.median()),
                "spread_mean": float(sp.mean()), "spread_max": int(sp.max()),
                "pct_sp1": float((sp == 1).mean() * 100),
                "pct_sp2": float((sp == 2).mean() * 100),
                "pct_sp3": float((sp == 3).mean() * 100),
                "pct_sp4plus": float((sp >= 4).mean() * 100),
            })
    return out


def hyd_fade_strategy():
    """Three variants of HYD fade-the-prior-tick strategy."""
    out = {}
    for day in (0, 1, 2):
        df = pd.read_csv(f"{DATA_DIR}/prices_round_3_day_{day}.csv", sep=";")
        h = df[df["product"] == "HYDROGEL_PACK"].sort_values("timestamp").reset_index(drop=True)
        b1 = h["bid_price_1"].astype(float).values
        a1 = h["ask_price_1"].astype(float).values
        bv1 = h["bid_volume_1"].fillna(0).astype(int).values
        av1 = h["ask_volume_1"].fillna(0).astype(int).values
        mid = (b1 + a1) / 2.0
        b2 = h["bid_price_2"].astype(float).values
        a2 = h["ask_price_2"].astype(float).values
        bv2 = h["bid_volume_2"].fillna(0).astype(int).values
        av2 = h["ask_volume_2"].fillna(0).astype(int).values

        # Variant A: market-take fade (passive). Only fire when prev tick |dx| >= 1
        for variant_name, params in [
            ("V_a_threshold_1", dict(thr=1.0, size=1)),
            ("V_b_threshold_2", dict(thr=2.0, size=2)),
            ("V_c_threshold_2_size4", dict(thr=2.0, size=4)),
        ]:
            pos = 0
            cash = 0.0
            trades = 0
            LIMIT = 200
            thr = params["thr"]
            size = params["size"]
            for i in range(1, len(h)):
                dx_prev = mid[i-1] - mid[i-2] if i >= 2 else 0
                if abs(dx_prev) < thr:
                    continue
                if dx_prev > 0 and pos > -LIMIT:
                    qty = min(int(bv1[i]), size, LIMIT + pos)
                    if qty > 0 and not np.isnan(b1[i]):
                        pos -= qty
                        cash += qty * b1[i]
                        trades += 1
                elif dx_prev < 0 and pos < LIMIT:
                    qty = min(int(av1[i]), size, LIMIT - pos)
                    if qty > 0 and not np.isnan(a1[i]):
                        pos += qty
                        cash -= qty * a1[i]
                        trades += 1
            last_mid = mid[-1]
            out.setdefault(variant_name, {})[day] = {
                "trades": trades, "pos_end": pos, "pnl": cash + pos * last_mid
            }
    return out


def hyd_offset_extreme_fade():
    """Fade-extreme-offset (offset > 2) only. Should win because mean(dx_next | offset>2) = -3.9."""
    out = {}
    for day in (0, 1, 2):
        df = pd.read_csv(f"{DATA_DIR}/prices_round_3_day_{day}.csv", sep=";")
        h = df[df["product"] == "HYDROGEL_PACK"].sort_values("timestamp").reset_index(drop=True)
        b1 = h["bid_price_1"].astype(float).values
        a1 = h["ask_price_1"].astype(float).values
        bv1 = h["bid_volume_1"].fillna(0).astype(int).values
        av1 = h["ask_volume_1"].fillna(0).astype(int).values
        b2 = h["bid_price_2"].astype(float).values
        a2 = h["ask_price_2"].astype(float).values
        bv2 = h["bid_volume_2"].fillna(0).astype(int).values
        av2 = h["ask_volume_2"].fillna(0).astype(int).values
        b3 = h["bid_price_3"].astype(float).values
        a3 = h["ask_price_3"].astype(float).values
        bv3 = h["bid_volume_3"].fillna(0).astype(int).values
        av3 = h["ask_volume_3"].fillna(0).astype(int).values

        # Wall = vol >= 15 (level-1 if so, else level-2, else level-3)
        wall_bid = np.where(bv1 >= 15, b1,
                    np.where(bv2 >= 15, b2,
                    np.where(bv3 >= 15, b3, b1)))
        wall_ask = np.where(av1 >= 15, a1,
                    np.where(av2 >= 15, a2,
                    np.where(av3 >= 15, a3, a1)))
        wall_mid = (wall_bid + wall_ask) / 2.0
        inner = (b1 + a1) / 2.0
        offset = inner - wall_mid

        for thr in [1.5, 2.0, 2.5]:
            pos = 0
            cash = 0.0
            trades = 0
            LIMIT = 200
            SIZE = 4
            for i in range(len(h)):
                if offset[i] >= thr and pos > -LIMIT:
                    qty = min(int(bv1[i]), SIZE, LIMIT + pos)
                    if qty > 0 and not np.isnan(b1[i]):
                        pos -= qty
                        cash += qty * b1[i]
                        trades += 1
                elif offset[i] <= -thr and pos < LIMIT:
                    qty = min(int(av1[i]), SIZE, LIMIT - pos)
                    if qty > 0 and not np.isnan(a1[i]):
                        pos += qty
                        cash -= qty * a1[i]
                        trades += 1
            out.setdefault(f"thr_{thr}", {})[day] = {
                "trades": trades, "pos_end": pos, "pnl": cash + pos * inner[-1]
            }
    return out


def trade_size_signature():
    """Bot signature: are most trade sizes equal to a fixed clip per product?"""
    out = []
    for day in (0, 1, 2):
        tr = pd.read_csv(f"{DATA_DIR}/trades_round_3_day_{day}.csv", sep=";")
        for prod in tr["symbol"].unique():
            sub = tr[tr["symbol"] == prod]
            if len(sub) < 5: continue
            modes = sub["quantity"].value_counts(normalize=True).head(5)
            top1 = modes.index[0]
            top1_pct = modes.values[0] * 100
            out.append({
                "day": day, "product": prod, "n": len(sub),
                "top_size": float(top1), "top_pct": float(top1_pct),
                "top5": modes.head(5).to_dict(),
                "mean_size": float(sub["quantity"].mean()),
                "max_size": int(sub["quantity"].max()),
            })
    return out


def vol_burst_regimes():
    """Detect regime shifts in HYD: rolling 200-tick std of dx."""
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    out = {}
    for day in (0, 1, 2):
        df = pd.read_csv(f"{DATA_DIR}/prices_round_3_day_{day}.csv", sep=";")
        h = df[df["product"] == "HYDROGEL_PACK"].sort_values("timestamp").reset_index(drop=True)
        mid = ((h["bid_price_1"] + h["ask_price_1"]) / 2).values
        dx = np.diff(mid)
        roll_std = pd.Series(np.abs(dx)).rolling(200).std().values
        # detect bursts: |dx| > 2 * baseline std
        baseline = roll_std[~np.isnan(roll_std)].mean()
        if baseline > 0:
            burst_thr = 2 * baseline
            burst_mask = roll_std > burst_thr
            n_bursts = (np.diff(np.concatenate([[False], burst_mask, [False]]).astype(int)) == 1).sum()
        else:
            n_bursts = 0
        out[day] = {"baseline_std": float(baseline), "n_bursts": int(n_bursts)}
        axes[day].plot(h["timestamp"].values[1:], roll_std, lw=0.5)
        axes[day].axhline(2 * baseline if baseline > 0 else 0, color="red", lw=0.5, ls="--")
        axes[day].set_title(f"HYD day {day}: rolling-200 |dx| std (red=2x baseline)")
        axes[day].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "10_hyd_vol_regimes.png"), dpi=110)
    plt.close()
    return out


def hyd_time_of_day():
    """Bin HYD into 10 windows; compute |dx| stats per window."""
    out = {}
    for day in (0, 1, 2):
        df = pd.read_csv(f"{DATA_DIR}/prices_round_3_day_{day}.csv", sep=";")
        h = df[df["product"] == "HYDROGEL_PACK"].sort_values("timestamp").reset_index(drop=True)
        mid = ((h["bid_price_1"] + h["ask_price_1"]) / 2).values
        dx = np.diff(mid)
        n = len(dx)
        bins = 10
        bin_size = n // bins
        per_bin = []
        for i in range(bins):
            seg = dx[i*bin_size:(i+1)*bin_size]
            per_bin.append(float(np.std(seg)))
        out[day] = per_bin
    return out


def main():
    sp = correct_spread_diagnostics()
    print("Spread diagnostics:")
    for r in sp:
        print(f"  d{r['day']} {r['product']:>22}: med={r['spread_med']:.1f} mean={r['spread_mean']:.2f} sp=1:{r['pct_sp1']:>5.1f}% sp=2:{r['pct_sp2']:>5.1f}% sp=3:{r['pct_sp3']:>5.1f}% sp>=4:{r['pct_sp4plus']:>5.1f}%")

    print("\nHYD prior-tick fade:")
    hf = hyd_fade_strategy()
    for variant, days in hf.items():
        for d, v in days.items():
            print(f"  {variant} d{d}: trades={v['trades']:>5} pos={v['pos_end']:>+4} pnl={v['pnl']:>+8.0f}")

    print("\nHYD offset-extreme fade:")
    of = hyd_offset_extreme_fade()
    for thr, days in of.items():
        for d, v in days.items():
            print(f"  {thr} d{d}: trades={v['trades']:>4} pos={v['pos_end']:>+4} pnl={v['pnl']:>+8.0f}")

    print("\nTrade size signatures:")
    sig = trade_size_signature()
    for r in sig:
        print(f"  d{r['day']} {r['product']:>22}: n={r['n']:>4} top_size={r['top_size']} ({r['top_pct']:.1f}%) mean={r['mean_size']:.2f} max={r['max_size']}")

    print("\nVol burst regimes:")
    vb = vol_burst_regimes()
    for d, v in vb.items():
        print(f"  d{d}: baseline_std={v['baseline_std']:.3f} n_bursts(>2x)={v['n_bursts']}")

    print("\nHYD time-of-day vol (10 bins):")
    tod = hyd_time_of_day()
    for d, bins in tod.items():
        print(f"  d{d}: {[f'{x:.2f}' for x in bins]}")

    out_all = {
        "spread": sp,
        "hyd_fade": hf,
        "hyd_offset_fade": of,
        "trade_signatures": sig,
        "vol_bursts": vb,
        "tod": tod,
    }
    with open(os.path.join(OUT_DIR, "final_diagnostics.json"), "w") as f:
        json.dump(out_all, f, indent=2)


if __name__ == "__main__":
    main()
