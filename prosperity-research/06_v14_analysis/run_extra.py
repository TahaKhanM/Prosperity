"""Extra vectorized analysis - per-strike smile residual + HYD wall-mid + sim PnL."""
import sys
import math
import json
import os
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/scripts/round3_options")
from bs import bs_call_price, implied_vol_call

DATA_DIR = "/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets/round3"
TTE_DAYS = {0: 8, 1: 7, 2: 6}
strikes_all = [5000, 5100, 5200, 5300, 5400, 5500]


def compute_iv_grid(day: int):
    df = pd.read_csv(f"{DATA_DIR}/prices_round_3_day_{day}.csv", sep=";")
    vfe = df[df["product"] == "VELVETFRUIT_EXTRACT"].set_index("timestamp")["mid_price"]
    t_yr = TTE_DAYS[day] / 365.0
    iv_df = pd.DataFrame(index=vfe.index)
    iv_df["S"] = vfe
    mid_df = pd.DataFrame(index=vfe.index)
    mid_df["S"] = vfe
    for K in strikes_all:
        v = df[df["product"] == f"VEV_{K}"].set_index("timestamp")["mid_price"]
        mid_df[f"K{K}"] = v
        # IV vector
        v_aligned = v.reindex(vfe.index)
        ivs = []
        for s, p in zip(vfe.values, v_aligned.values):
            if math.isnan(p):
                ivs.append(np.nan)
                continue
            iv = implied_vol_call(float(p), float(s), float(K), t_yr)
            ivs.append(iv if iv is not None and not math.isnan(iv) else np.nan)
        iv_df[f"K{K}"] = ivs
    return df, iv_df, mid_df, t_yr


def per_strike_residuals():
    """For each timestamp, fit smile excluding the target strike, compute residual."""
    out = []
    for day in (0, 1, 2):
        print(f"  loading day {day}...")
        prices, iv_df, mid_df, t_yr = compute_iv_grid(day)
        common = iv_df.dropna().index  # all 6 strikes valid
        S_arr = iv_df.loc[common, "S"].values
        for target_K in strikes_all:
            others = [k for k in strikes_all if k != target_K]
            iv_others = iv_df.loc[common, [f"K{k}" for k in others]].values  # (n, 5)
            # log-moneyness vectorized: ln(K/S)
            n = len(common)
            x_others = np.log(np.array(others)[None, :] / S_arr[:, None])  # (n, 5)
            # quadratic fit per row
            # vectorized with stacked least squares
            A = np.stack([np.ones_like(x_others), x_others, x_others ** 2], axis=2)  # (n, 5, 3)
            # solve for coefs: A @ c ~ iv_others
            coefs = np.zeros((n, 3))
            for i in range(n):
                try:
                    c, *_ = np.linalg.lstsq(A[i], iv_others[i], rcond=None)
                    coefs[i] = c
                except Exception:
                    coefs[i] = np.nan
            x_target = np.log(target_K / S_arr)
            iv_target = coefs[:, 0] + coefs[:, 1] * x_target + coefs[:, 2] * x_target ** 2
            # BS prices vectorized
            fair_prices = np.array([bs_call_price(float(s), float(target_K), t_yr, float(iv))
                                     for s, iv in zip(S_arr, iv_target)])
            actual = mid_df.loc[common, f"K{target_K}"].values
            resid = actual - fair_prices
            n1k = min(1000, len(resid))
            out.append({
                "day": day, "K": target_K, "n": len(resid),
                "mean": float(np.nanmean(resid)),
                "med": float(np.nanmedian(resid)),
                "first": float(np.nanmean(resid[:n1k])),
                "last": float(np.nanmean(resid[-n1k:])),
                "abs_max": float(np.nanmax(np.abs(resid))),
                "p10": float(np.nanpercentile(resid, 10)),
                "p90": float(np.nanpercentile(resid, 90)),
            })
    return out


def hyd_wall_mid():
    """HYD wall-mid analysis and sim."""
    out = {}
    for day in (0, 1, 2):
        df = pd.read_csv(f"{DATA_DIR}/prices_round_3_day_{day}.csv", sep=";")
        h = df[df["product"] == "HYDROGEL_PACK"].sort_values("timestamp").copy().reset_index(drop=True)
        # vectorized wall computation
        b1 = h["bid_price_1"].astype(float)
        a1 = h["ask_price_1"].astype(float)
        bv1 = h["bid_volume_1"].fillna(0).astype(float)
        av1 = h["ask_volume_1"].fillna(0).astype(float)
        b2 = h["bid_price_2"].astype(float)
        a2 = h["ask_price_2"].astype(float)
        # wall_bid: b1 if bv1>=15 else b2 (or b1 if b2 nan)
        wall_bid = np.where(bv1 >= 15, b1, np.where(b2.notna(), b2, b1))
        wall_ask = np.where(av1 >= 15, a1, np.where(a2.notna(), a2, a1))
        wall_mid = (wall_bid + wall_ask) / 2.0
        inner_mid = (b1 + a1) / 2.0
        offset = inner_mid - wall_mid
        # Predictive: offset(t) -> dx(t+1)
        dx_next = inner_mid.diff().shift(-1)
        valid = (~np.isnan(offset)) & (~np.isnan(dx_next))
        x, y = offset[valid].values, dx_next[valid].values
        if x.var() > 0:
            r = np.corrcoef(x, y)[0, 1]
            beta = np.cov(x, y)[0, 1] / x.var()
        else:
            r, beta = np.nan, np.nan
        # Sim
        pos, cash, trades = 0, 0.0, 0
        LIMIT, TAKE = 200, 4
        for i in range(len(h)):
            bid = b1.iloc[i]; ask = a1.iloc[i]
            fair = wall_mid[i]
            if not np.isnan(ask) and ask <= fair - 0.5 and pos < LIMIT:
                qty = min(int(av1.iloc[i]), TAKE, LIMIT - pos)
                if qty > 0:
                    pos += qty; cash -= qty * ask; trades += 1
            if not np.isnan(bid) and bid >= fair + 0.5 and pos > -LIMIT:
                qty = min(int(bv1.iloc[i]), TAKE, LIMIT + pos)
                if qty > 0:
                    pos -= qty; cash += qty * bid; trades += 1
        last_mid = h.iloc[-1]["mid_price"]
        out[day] = {
            "trades": trades,
            "pos_end": pos,
            "pnl": cash + pos * last_mid,
            "offset_mean": float(np.nanmean(offset)),
            "offset_std": float(np.nanstd(offset)),
            "abs_offset_pct": float((offset != 0).mean() * 100) if not np.all(np.isnan(offset)) else 0.0,
            "corr_offset_dxnext": float(r) if not np.isnan(r) else None,
            "beta": float(beta) if not np.isnan(beta) else None,
        }
    return out


def smile_mm_sim_v5100():
    """Simulate naive smile-MM strategy on V5100 across all 3 days."""
    out = {}
    for day in (0, 1, 2):
        prices, iv_df, mid_df, t_yr = compute_iv_grid(day)
        v51 = prices[prices["product"] == "VEV_5100"].set_index("timestamp")[["bid_price_1","bid_volume_1","ask_price_1","ask_volume_1","mid_price"]]
        common = iv_df.dropna().index.intersection(v51.index)
        common = sorted(common)
        S_arr = iv_df.loc[common, "S"].values
        # smile from other 5 strikes
        others = [k for k in strikes_all if k != 5100]
        iv_others = iv_df.loc[common, [f"K{k}" for k in others]].values
        n = len(common)
        x_others = np.log(np.array(others)[None, :] / S_arr[:, None])
        A = np.stack([np.ones_like(x_others), x_others, x_others**2], axis=2)
        fair_arr = np.zeros(n)
        for i in range(n):
            c, *_ = np.linalg.lstsq(A[i], iv_others[i], rcond=None)
            x51 = np.log(5100.0 / S_arr[i])
            iv51 = c[0] + c[1] * x51 + c[2] * x51**2
            fair_arr[i] = bs_call_price(float(S_arr[i]), 5100.0, t_yr, float(iv51))
        # Sim: take ask if ask <= fair - 0.5; hit bid if bid >= fair + 0.5
        v51c = v51.loc[common]
        pos, cash, trades = 0, 0.0, 0
        LIMIT, TAKE = 300, 4
        pos_path = []
        residuals = []
        for i, ts in enumerate(common):
            bid = v51c.loc[ts, "bid_price_1"]
            ask = v51c.loc[ts, "ask_price_1"]
            bv = v51c.loc[ts, "bid_volume_1"] if not pd.isna(v51c.loc[ts, "bid_volume_1"]) else 0
            av = v51c.loc[ts, "ask_volume_1"] if not pd.isna(v51c.loc[ts, "ask_volume_1"]) else 0
            mid = v51c.loc[ts, "mid_price"]
            fair = fair_arr[i]
            residuals.append(mid - fair)
            if not pd.isna(ask) and ask <= fair - 0.5 and pos < LIMIT:
                qty = min(int(av), TAKE, LIMIT - pos)
                if qty > 0:
                    pos += qty; cash -= qty * ask; trades += 1
            if not pd.isna(bid) and bid >= fair + 0.5 and pos > -LIMIT:
                qty = min(int(bv), TAKE, LIMIT + pos)
                if qty > 0:
                    pos -= qty; cash += qty * bid; trades += 1
            pos_path.append(pos)
        last_mid = v51c.iloc[-1]["mid_price"]
        residuals = np.array(residuals)
        out[day] = {
            "trades": trades, "pos_end": pos,
            "pnl": cash + pos * last_mid,
            "max_long": int(max(pos_path)), "max_short": int(min(pos_path)),
            "frac_short_cap": float(sum(1 for p in pos_path if p <= -LIMIT) / len(pos_path)),
            "frac_long_cap": float(sum(1 for p in pos_path if p >= LIMIT) / len(pos_path)),
            "resid_mean": float(np.nanmean(residuals)),
            "resid_med": float(np.nanmedian(residuals)),
            "frac_rich": float((residuals > 0.5).mean()),
            "frac_cheap": float((residuals < -0.5).mean()),
        }
    return out


def main():
    print("Per-strike residuals...")
    per_strike = per_strike_residuals()
    print("HYD wall-mid analysis...")
    wall = hyd_wall_mid()
    print("V5100 smile MM sim...")
    sim = smile_mm_sim_v5100()
    out = {"per_strike": per_strike, "wall_mid": wall, "v5100_sim": sim}
    with open("/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_v14_analysis/extra_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print("Wrote extra_results.json")
    # also print key tables
    print("\n=== Per-strike residuals ===")
    print(f"{'day':>3} {'K':>5} {'mean':>8} {'med':>8} {'first':>8} {'last':>8} {'abs_max':>8} {'p10':>8} {'p90':>8}")
    for r in per_strike:
        print(f"{r['day']:>3} {r['K']:>5} {r['mean']:+8.3f} {r['med']:+8.3f} {r['first']:+8.3f} {r['last']:+8.3f} {r['abs_max']:8.3f} {r['p10']:+8.3f} {r['p90']:+8.3f}")
    print("\n=== HYD wall-mid sim ===")
    for d, v in wall.items():
        print(f"day {d}: {v}")
    print("\n=== V5100 smile-MM sim ===")
    for d, v in sim.items():
        print(f"day {d}: {v}")


if __name__ == "__main__":
    main()
