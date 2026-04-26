"""Regime detection: when is HYDROGEL trending vs anchored?

Goal: identify the day-1 trend regime that costs v10 1.5k vs v9 (which loses
even more on the rigid anchor when HYD trends to 10080).
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


ROOT = Path("/Users/tahakhan/Documents/Work/Projects/Prosperity")
DATA = ROOT / "Data" / "ROUND_3"
OUT = ROOT / "prosperity-research" / "05_v10_replay_analysis"


def load_mids(d, sym):
    rows = []
    with open(DATA / f"prices_round_3_day_{d}.csv") as f:
        r = csv.DictReader(f, delimiter=";")
        for row in r:
            if row["product"] != sym:
                continue
            ts = int(row["timestamp"])
            mid = float(row["mid_price"]) if row["mid_price"] else None
            if mid is not None:
                rows.append((ts, mid))
    return rows


def ema(xs, alpha, seed=None):
    out = []
    e = xs[0] if seed is None else seed
    for x in xs:
        e = (1 - alpha) * e + alpha * x
        out.append(e)
    return np.array(out)


def anchor_pnl_sim(mids, fair_fn, take_edge=4):
    """Tiny ad-hoc HYD MM simulator: take when ask <= fair-take_edge or
    bid >= fair+take_edge; mark to next-tick mid.  Position cap 200.

    fair_fn(t, m) → fair value at tick t given current mid m and history (state stored on fn).
    Returns total mark-to-market PnL.
    """
    pos = 0
    cash = 0
    cap = 200
    pnls = []
    for i in range(len(mids) - 1):
        m = mids[i]
        bid = m - 8  # approx - real bid ~7-8 below mid for HYD
        ask = m + 8
        fair = fair_fn(i, m)
        take = 0
        if ask + take_edge <= fair and pos < cap:
            qty = min(20, cap - pos)
            cash -= ask * qty
            pos += qty
            take = +qty
        elif bid - take_edge >= fair and pos > -cap:
            qty = min(20, cap + pos)
            cash += bid * qty
            pos -= qty
            take = -qty
        next_mid = mids[i + 1]
        pnls.append(cash + pos * next_mid)
    return pnls[-1] if pnls else 0


# Simulate fair functions on each day:

class V9Fair:
    def __init__(self, anchor=10000.0, A_W=0.40, alpha=0.10):
        self.anchor = anchor
        self.A_W = A_W
        self.alpha = alpha
        self.fair = None
    def __call__(self, t, m):
        blend = self.A_W * self.anchor + (1 - self.A_W) * m
        if self.fair is None:
            self.fair = blend
        else:
            self.fair = (1 - self.alpha) * self.fair + self.alpha * blend
        return self.fair


class AdaptiveFair:
    """Slow EMA bounded to [lo, hi] used as effective anchor instead of rigid 10000."""
    def __init__(self, lo=9970, hi=10030, A_W=0.40, alpha=0.10, slow_alpha=0.005):
        self.lo = lo
        self.hi = hi
        self.A_W = A_W
        self.alpha = alpha
        self.slow_alpha = slow_alpha
        self.slow = None
        self.fair = None
    def __call__(self, t, m):
        if self.slow is None:
            self.slow = m
        else:
            self.slow = (1 - self.slow_alpha) * self.slow + self.slow_alpha * m
        eff_anchor = max(self.lo, min(self.hi, self.slow))
        blend = self.A_W * eff_anchor + (1 - self.A_W) * m
        if self.fair is None:
            self.fair = blend
        else:
            self.fair = (1 - self.alpha) * self.fair + self.alpha * blend
        return self.fair


class TrendDetectFair:
    """When |slow_EMA - 10000| > threshold, drop anchor weight to 0."""
    def __init__(self, anchor=10000.0, A_W=0.40, alpha=0.10, slow_alpha=0.005,
                 thr_lo=20, thr_hi=60):
        self.anchor = anchor
        self.A_W = A_W
        self.alpha = alpha
        self.slow_alpha = slow_alpha
        self.thr_lo = thr_lo
        self.thr_hi = thr_hi
        self.slow = None
        self.fair = None
    def __call__(self, t, m):
        if self.slow is None:
            self.slow = m
        else:
            self.slow = (1 - self.slow_alpha) * self.slow + self.slow_alpha * m
        # taper anchor weight down as |slow - anchor| crosses thr_lo..thr_hi
        dev = abs(self.slow - self.anchor)
        taper = max(0.0, min(1.0, 1 - max(0.0, dev - self.thr_lo) / (self.thr_hi - self.thr_lo)))
        A_eff = self.A_W * taper
        # When anchor weight collapses, anchor itself becomes irrelevant; fair = micro.
        anchor_used = self.anchor if taper > 0 else m
        blend = A_eff * anchor_used + (1 - A_eff) * m
        if self.fair is None:
            self.fair = blend
        else:
            self.fair = (1 - self.alpha) * self.fair + self.alpha * blend
        return self.fair


def main():
    # Plot HYDROGEL with v9 fair vs adaptive fair
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=False)
    print("\n=== HYD ad-hoc MM PnL by fair model ===")
    print(f"{'fair':25s}  d0       d1       d2     total")

    fairs = [
        ("v9_anchor_10000", lambda: V9Fair()),
        ("adaptive_lo9970_hi10030", lambda: AdaptiveFair(lo=9970, hi=10030, A_W=0.40, slow_alpha=0.005)),
        ("adaptive_lo9980_hi10010", lambda: AdaptiveFair(lo=9980, hi=10010, A_W=0.40, slow_alpha=0.005)),
        ("trend_detect_thr20_60",   lambda: TrendDetectFair(thr_lo=20, thr_hi=60, slow_alpha=0.005)),
        ("trend_detect_thr30_80",   lambda: TrendDetectFair(thr_lo=30, thr_hi=80, slow_alpha=0.005)),
        ("trend_detect_thr15_40",   lambda: TrendDetectFair(thr_lo=15, thr_hi=40, slow_alpha=0.005)),
        ("pure_micro_no_anchor",     lambda: V9Fair(A_W=0.0)),
    ]
    for name, factory in fairs:
        totals = []
        for d in (0, 1, 2):
            mids = [m for _, m in load_mids(d, "HYDROGEL_PACK")]
            ff = factory()
            tot = anchor_pnl_sim(mids, ff)
            totals.append(tot)
        print(f"  {name:25s}  {totals[0]:7.0f}  {totals[1]:7.0f}  {totals[2]:7.0f}  {sum(totals):7.0f}")

    # Plot day 1 HYD with v9 fair and adaptive fair
    for di, d in enumerate((0, 1, 2)):
        mids_full = load_mids(d, "HYDROGEL_PACK")
        ts = np.array([t for t, _ in mids_full])
        mids = np.array([m for _, m in mids_full])
        ax = axes[di]
        ax.plot(ts, mids, color="black", lw=0.6, alpha=0.7, label="mid")
        # v9 fair
        ff = V9Fair()
        v9f = np.array([ff(i, m) for i, m in enumerate(mids)])
        # adaptive fair
        ff = AdaptiveFair(lo=9970, hi=10030, slow_alpha=0.005)
        adapt = np.array([ff(i, m) for i, m in enumerate(mids)])
        # trend detect
        ff = TrendDetectFair(thr_lo=20, thr_hi=60)
        td = np.array([ff(i, m) for i, m in enumerate(mids)])
        ax.plot(ts, v9f, color="red", lw=1.0, alpha=0.8, label="v9 fair")
        ax.plot(ts, adapt, color="blue", lw=1.0, alpha=0.8, label="adaptive(9970-10030)")
        ax.plot(ts, td, color="green", lw=1.0, alpha=0.8, label="trend_detect(20-60)")
        ax.axhline(10000, color="grey", lw=0.5, ls=":")
        ax.set_title(f"Day {d}: HYDROGEL mid vs fair value models")
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT / "hyd_fair_models.png", dpi=120)
    plt.close()
    print("\nWrote hyd_fair_models.png")


if __name__ == "__main__":
    main()
