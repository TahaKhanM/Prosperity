"""Phase 1 lens battery — comprehensive per-product diagnostics for R4.

Usage:
    python3 scripts/round4_options/lens_battery.py <PRODUCT> [days...]
    e.g. python3 scripts/round4_options/lens_battery.py HYDROGEL_PACK 1 2 3

For each product / day combination, prints:
- Lens A (distributional): mean/median/std/IQR/skew/kurt of mid; spread distribution; depth occupancy.
- Lens B (time-series): rho1..rho50, OU half-life, variance ratio at k in {2,5,10,50,200},
  Hurst exponent, top spectral peaks, simple cusum change-points.
- Lens C (microstructure): imbalance@1/2/3, microprice vs mid, wall-mid vs mid, queue-depth correlations.
- Lens D (counterparty): per-Mark conditional next-{1,5,20,100}-tick mid return given a print on this side,
  with per-Mark trade-counts so we can flag thin samples.
- Lens E (cross-asset): same-tick & lead-lag with VELVETFRUIT_EXTRACT (vouchers only).
- Lens F (weird): bimodality flag, longest run of unchanged mids, ticks where book briefly empties.

All outputs go to stdout as Markdown blocks so sub-agents can paste them into per_product/<symbol>.md.

Stdlib only.
"""

from __future__ import annotations

import csv
import math
import os
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

# Allow `from stat_tests import ...`.
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stat_tests import (  # noqa: E402
    rho1,
    ou_half_life,
    variance_ratio,
    hurst,
    spectral_peak,
)

DATA_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "datasets", "round4"))


# --------------------------------------------------------------------------- IO


def _row_to_floats(row: List[str]) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    for v in row:
        if v == "" or v is None:
            out.append(None)
            continue
        try:
            out.append(float(v))
        except ValueError:
            out.append(None)
    return out


def load_prices(product: str, day: int) -> List[Dict[str, Optional[float]]]:
    """Return list of dicts in time order, one per snapshot.

    Each dict has: ts, b1, bv1, b2, bv2, b3, bv3, a1, av1, a2, av2, a3, av3, mid
    (volumes positive on both sides for convenience).
    """
    path = os.path.join(DATA_DIR, f"prices_round_4_day_{day}.csv")
    rows: List[Dict[str, Optional[float]]] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for r in reader:
            if r.get("product") != product:
                continue
            try:
                ts = int(r["timestamp"])
            except Exception:
                continue
            d = {"ts": ts}
            for col, key in [
                ("bid_price_1", "b1"), ("bid_volume_1", "bv1"),
                ("bid_price_2", "b2"), ("bid_volume_2", "bv2"),
                ("bid_price_3", "b3"), ("bid_volume_3", "bv3"),
                ("ask_price_1", "a1"), ("ask_volume_1", "av1"),
                ("ask_price_2", "a2"), ("ask_volume_2", "av2"),
                ("ask_price_3", "a3"), ("ask_volume_3", "av3"),
                ("mid_price", "mid"),
            ]:
                v = r.get(col)
                d[key] = float(v) if v not in (None, "") else None
            rows.append(d)
    rows.sort(key=lambda r: r["ts"])
    return rows


def load_trades(product: str, day: int) -> List[Dict[str, object]]:
    path = os.path.join(DATA_DIR, f"trades_round_4_day_{day}.csv")
    rows: List[Dict[str, object]] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for r in reader:
            if r.get("symbol") != product:
                continue
            try:
                rows.append({
                    "ts": int(r["timestamp"]),
                    "buyer": r.get("buyer", "") or "",
                    "seller": r.get("seller", "") or "",
                    "price": float(r["price"]),
                    "qty": float(r["quantity"]),
                })
            except Exception:
                continue
    rows.sort(key=lambda r: r["ts"])
    return rows


# --------------------------------------------------------------------------- A


def quantiles(xs: List[float]) -> Tuple[float, float, float]:
    """Return (q25, median, q75)."""
    if not xs:
        return (float("nan"),) * 3
    s = sorted(xs)
    def q(p):
        i = p * (len(s) - 1)
        lo, hi = int(math.floor(i)), int(math.ceil(i))
        return s[lo] if lo == hi else s[lo] * (hi - i) + s[hi] * (i - lo)
    return q(0.25), q(0.5), q(0.75)


def std(xs: List[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def skew(xs: List[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    m = sum(xs) / n
    s = std(xs)
    if s == 0:
        return float("nan")
    return sum(((x - m) / s) ** 3 for x in xs) * n / ((n - 1) * (n - 2))


def kurt_excess(xs: List[float]) -> float:
    n = len(xs)
    if n < 4:
        return float("nan")
    m = sum(xs) / n
    s = std(xs)
    if s == 0:
        return float("nan")
    g = sum(((x - m) / s) ** 4 for x in xs) / n
    return g - 3.0  # excess kurtosis


def lens_a(prices: List[Dict], product: str, day: int) -> str:
    mids = [p["mid"] for p in prices if p.get("mid") is not None]
    if not mids:
        return f"### Day {day} — Lens A — no mids\n"
    spreads = [p["a1"] - p["b1"] for p in prices if p.get("a1") and p.get("b1")]
    depths_b = sum(1 for p in prices if p.get("b2") is not None)
    depths_a = sum(1 for p in prices if p.get("a2") is not None)
    depths_b3 = sum(1 for p in prices if p.get("b3") is not None)
    depths_a3 = sum(1 for p in prices if p.get("a3") is not None)
    crossed = sum(1 for p in prices if p.get("a1") and p.get("b1") and p["a1"] <= p["b1"])
    one_tick = max((abs(mids[i] - mids[i - 1]) for i in range(1, len(mids))), default=0.0)

    # longest run of unchanged mids
    longest = cur = 1
    for i in range(1, len(mids)):
        if mids[i] == mids[i - 1]:
            cur += 1
            if cur > longest:
                longest = cur
        else:
            cur = 1

    q25, med, q75 = quantiles(mids)
    sq25, smed, sq75 = quantiles(spreads) if spreads else (float("nan"),) * 3
    return (
        f"### Day {day} — Lens A (distributional)\n"
        f"- mids n={len(mids)}, mean={sum(mids)/len(mids):.3f}, median={med:.3f}, "
        f"std={std(mids):.3f}, IQR=[{q25:.3f}, {q75:.3f}], range=[{min(mids):.3f}, {max(mids):.3f}]\n"
        f"- skew={skew(mids):.3f}, excess kurt={kurt_excess(mids):.3f}\n"
        f"- spread (a1-b1) median={smed:.3f}, IQR=[{sq25:.3f}, {sq75:.3f}]\n"
        f"- ticks with level-2 bid={depths_b}/{len(prices)}, ask={depths_a}/{len(prices)}, "
        f"level-3 bid={depths_b3}, ask={depths_a3}\n"
        f"- crossed/locked-book ticks={crossed}\n"
        f"- max one-tick |Δmid|={one_tick:.2f}, longest run unchanged mid={longest} ticks\n"
    )


# --------------------------------------------------------------------------- B


def autocorr(series: Sequence[float], lag: int) -> float:
    n = len(series)
    if n <= lag + 1:
        return float("nan")
    m = sum(series) / n
    num = sum((series[i] - m) * (series[i - lag] - m) for i in range(lag, n))
    den = sum((v - m) ** 2 for v in series)
    return num / den if den > 0 else float("nan")


def cusum_break(xs: Sequence[float]) -> Tuple[int, float]:
    """Return (index, abs_max_cusum) of the largest mean-shift candidate."""
    if len(xs) < 4:
        return (0, 0.0)
    m = sum(xs) / len(xs)
    cs = 0.0
    best_i, best_v = 0, 0.0
    for i, v in enumerate(xs):
        cs += v - m
        if abs(cs) > best_v:
            best_v = abs(cs)
            best_i = i
    return best_i, best_v


def lens_b(prices: List[Dict], day: int) -> str:
    mids = [p["mid"] for p in prices if p.get("mid") is not None]
    if len(mids) < 100:
        return f"### Day {day} — Lens B — too few mids\n"
    rets = [mids[i] - mids[i - 1] for i in range(1, len(mids))]
    rs = {k: f"{autocorr(rets, k):+.4f}" for k in (1, 2, 3, 5, 10, 20, 50)}
    hl = ou_half_life(mids)
    h = hurst(mids)
    vrs = {k: variance_ratio(mids, k) for k in (2, 5, 10, 50, 200) if k * 2 < len(rets)}
    period, power = spectral_peak(mids[: min(2000, len(mids))])  # truncate for speed
    cb_i, cb_v = cusum_break(rets)
    return (
        f"### Day {day} — Lens B (time-series)\n"
        f"- return autocorr: ρ1={rs[1]} ρ2={rs[2]} ρ3={rs[3]} ρ5={rs[5]} ρ10={rs[10]} "
        f"ρ20={rs[20]} ρ50={rs[50]}\n"
        f"- OU half-life on mid (ticks)={hl:.1f}, Hurst={h:.3f}\n"
        f"- variance ratio: {', '.join(f'k={k}:{v:.3f}' for k, v in vrs.items())}\n"
        f"- spectral peak period (samples) on first 2k mids = {period}, power={power:.1f}\n"
        f"- largest CUSUM break at index ~{cb_i}, |CUSUM|={cb_v:.1f}\n"
    )


# --------------------------------------------------------------------------- C


def _imb_n(p: Dict, n: int) -> Optional[float]:
    bv = 0.0
    av = 0.0
    for k in range(1, n + 1):
        b = p.get(f"bv{k}")
        a = p.get(f"av{k}")
        if b is not None:
            bv += b
        if a is not None:
            av += abs(a)
    t = bv + av
    return None if t <= 0 else (bv - av) / t


def _microprice(p: Dict) -> Optional[float]:
    if p.get("b1") is None or p.get("a1") is None:
        return None
    bv = p.get("bv1") or 0
    av = abs(p.get("av1") or 0)
    t = bv + av
    if t <= 0:
        return (p["b1"] + p["a1"]) / 2
    return (p["a1"] * bv + p["b1"] * av) / t


def _wall_mid(p: Dict) -> Optional[float]:
    bids: List[Tuple[float, float]] = []
    asks: List[Tuple[float, float]] = []
    for k in range(1, 4):
        bp, bv = p.get(f"b{k}"), p.get(f"bv{k}")
        ap, av = p.get(f"a{k}"), p.get(f"av{k}")
        if bp is not None and bv is not None:
            bids.append((bp, bv))
        if ap is not None and av is not None:
            asks.append((ap, abs(av)))
    if not bids or not asks:
        return None
    wb = max(bids, key=lambda x: x[1])[0]
    wa = max(asks, key=lambda x: x[1])[0]
    return (wb + wa) / 2.0


def lens_c(prices: List[Dict], day: int) -> str:
    """Microstructure: cross-correlate imbalance at top-1/2/3 with next-h-tick returns."""
    horizons = [1, 5, 20]
    series = []
    for p in prices:
        if p.get("mid") is None:
            continue
        series.append({
            "mid": p["mid"],
            "imb1": _imb_n(p, 1),
            "imb2": _imb_n(p, 2),
            "imb3": _imb_n(p, 3),
            "micro": _microprice(p),
            "wall": _wall_mid(p),
        })
    n = len(series)
    if n < 100:
        return f"### Day {day} — Lens C — too few rows\n"

    def corr_with_future_return(key: str, h: int) -> Tuple[float, float, int]:
        """Return (mean_signal, t-stat, n_used)."""
        x: List[float] = []
        y: List[float] = []
        for i in range(n - h):
            s = series[i].get(key)
            r = series[i + h]["mid"] - series[i]["mid"]
            if s is None:
                continue
            x.append(s)
            y.append(r)
        m = len(x)
        if m < 30:
            return float("nan"), float("nan"), m
        # OLS slope & t-stat (no intercept simplification: use centered)
        mx = sum(x) / m
        my = sum(y) / m
        cov = sum((x[i] - mx) * (y[i] - my) for i in range(m))
        sx2 = sum((x[i] - mx) ** 2 for i in range(m))
        if sx2 == 0:
            return float("nan"), float("nan"), m
        beta = cov / sx2
        # residual std
        resid2 = sum((y[i] - my - beta * (x[i] - mx)) ** 2 for i in range(m))
        if m < 3:
            return beta, float("nan"), m
        sigma2 = resid2 / (m - 2)
        se = math.sqrt(sigma2 / sx2) if sx2 > 0 else float("nan")
        t = beta / se if se and se > 0 else float("nan")
        return beta, t, m

    out = [f"### Day {day} — Lens C (microstructure)"]
    for k in ("imb1", "imb2", "imb3"):
        for h in horizons:
            b, t, m = corr_with_future_return(k, h)
            out.append(f"- {k} → Δmid_{{t+{h}}}: β={b:+.4f} t={t:+.2f} (n={m})")

    # microprice and wall-mid as fair-value predictors
    def fv_predict_test(field: str) -> Tuple[float, float, int]:
        x = []
        y = []
        for i in range(n - 1):
            s = series[i].get(field)
            mid = series[i]["mid"]
            r = series[i + 1]["mid"] - mid
            if s is None:
                continue
            x.append(s - mid)  # deviation
            y.append(r)
        if len(x) < 30:
            return float("nan"), float("nan"), len(x)
        m = len(x)
        mx = sum(x) / m
        my = sum(y) / m
        cov = sum((x[i] - mx) * (y[i] - my) for i in range(m))
        sx2 = sum((x[i] - mx) ** 2 for i in range(m))
        if sx2 == 0:
            return float("nan"), float("nan"), m
        beta = cov / sx2
        resid2 = sum((y[i] - my - beta * (x[i] - mx)) ** 2 for i in range(m))
        if m < 3:
            return beta, float("nan"), m
        se = math.sqrt(resid2 / (m - 2) / sx2)
        return beta, beta / se if se > 0 else float("nan"), m

    for k in ("micro", "wall"):
        b, t, m = fv_predict_test(k)
        out.append(f"- ({k}-mid) → Δmid_{{t+1}}: β={b:+.4f} t={t:+.2f} (n={m})")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- D


def lens_d(prices: List[Dict], trades: List[Dict], day: int) -> str:
    """Per-Mark conditional next-h-tick mid return given a buy/sell print."""
    horizons = [1, 5, 20, 100]
    by_ts: Dict[int, float] = {}
    for p in prices:
        if p.get("mid") is not None:
            by_ts[p["ts"]] = p["mid"]
    sorted_ts = sorted(by_ts)
    if not sorted_ts:
        return f"### Day {day} — Lens D — no mids\n"
    # binary-search helper
    def mid_at_or_after(ts: int) -> Optional[float]:
        lo, hi = 0, len(sorted_ts) - 1
        if ts > sorted_ts[-1]:
            return None
        while lo < hi:
            mid_i = (lo + hi) // 2
            if sorted_ts[mid_i] < ts:
                lo = mid_i + 1
            else:
                hi = mid_i
        return by_ts[sorted_ts[lo]]

    # marks observed
    marks_b: Dict[str, List[Tuple[int, float, float]]] = defaultdict(list)  # mark -> (ts, signed_qty, price)
    marks_s: Dict[str, List[Tuple[int, float, float]]] = defaultdict(list)
    for t in trades:
        b = t.get("buyer") or ""
        s = t.get("seller") or ""
        if b.startswith("Mark "):
            marks_b[b].append((t["ts"], t["qty"], t["price"]))
        if s.startswith("Mark "):
            marks_s[s].append((t["ts"], t["qty"], t["price"]))

    all_marks = sorted(set(marks_b) | set(marks_s))
    out = [f"### Day {day} — Lens D (counterparty conditional return)"]
    out.append("| Mark | side | n | mean_qty | h=1 mean Δmid | h=5 | h=20 | h=100 |")
    out.append("|---|---|---|---|---|---|---|---|")
    for m in all_marks:
        for label, src in (("buy", marks_b.get(m, [])), ("sell", marks_s.get(m, []))):
            if not src:
                continue
            qtys = [q for _, q, _ in src]
            avg_q = sum(qtys) / len(qtys)
            row_vals = [f"{m}", label, str(len(src)), f"{avg_q:.1f}"]
            for h in horizons:
                ds = []
                for ts, _, _ in src:
                    target = ts + h * 100
                    cur = mid_at_or_after(ts)
                    fut = mid_at_or_after(target)
                    if cur is None or fut is None:
                        continue
                    ds.append(fut - cur)
                if not ds:
                    row_vals.append("—")
                    continue
                mu = sum(ds) / len(ds)
                if len(ds) > 2:
                    sd = std(ds)
                    se = sd / math.sqrt(len(ds))
                    t_stat = mu / se if se > 0 else float("nan")
                else:
                    t_stat = float("nan")
                row_vals.append(f"{mu:+.2f} (t={t_stat:+.1f})")
            out.append("| " + " | ".join(row_vals) + " |")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- E


def _build_ve_mid_index(day: int) -> Tuple[List[int], List[float]]:
    rows = load_prices("VELVETFRUIT_EXTRACT", day)
    ts = []
    mids = []
    for r in rows:
        if r.get("mid") is None:
            continue
        ts.append(r["ts"])
        mids.append(r["mid"])
    return ts, mids


def lens_e(prices: List[Dict], product: str, day: int) -> str:
    if product == "VELVETFRUIT_EXTRACT" or product == "HYDROGEL_PACK":
        return ""
    ve_ts, ve_mids = _build_ve_mid_index(day)
    if not ve_ts:
        return f"### Day {day} — Lens E — no VE\n"
    ve_index = {t: m for t, m in zip(ve_ts, ve_mids)}
    pairs: List[Tuple[float, float]] = []
    for r in prices:
        m = r.get("mid")
        if m is None:
            continue
        ve = ve_index.get(r["ts"])
        if ve is None:
            continue
        pairs.append((m, ve))
    if len(pairs) < 100:
        return f"### Day {day} — Lens E — too few aligned ticks\n"
    # Same-tick correlation of returns
    vr = [pairs[i][0] - pairs[i - 1][0] for i in range(1, len(pairs))]
    vs = [pairs[i][1] - pairs[i - 1][1] for i in range(1, len(pairs))]
    n = len(vr)
    mr = sum(vr) / n
    ms = sum(vs) / n
    cov = sum((vr[i] - mr) * (vs[i] - ms) for i in range(n))
    sr = math.sqrt(sum((vr[i] - mr) ** 2 for i in range(n)))
    ss = math.sqrt(sum((vs[i] - ms) ** 2 for i in range(n)))
    rho = cov / (sr * ss) if (sr * ss) > 0 else float("nan")

    # Lead-lag: corr(Δprod_t, ΔVE_{t+k}) for k in -5..+5
    out = [f"### Day {day} — Lens E (cross-asset with VE)"]
    out.append(f"- same-tick return corr ρ(Δ{product}, ΔVE) = {rho:+.4f} (n={n})")
    leads = []
    for k in (-3, -2, -1, 0, 1, 2, 3, 5):
        if k == 0:
            continue
        n_eff = n - abs(k)
        if n_eff < 100:
            continue
        if k > 0:
            xs = vr[:n_eff]
            ys = vs[k:k + n_eff]
        else:
            xs = vr[-k:]
            ys = vs[:n_eff]
        mx = sum(xs) / n_eff
        my = sum(ys) / n_eff
        cv = sum((xs[i] - mx) * (ys[i] - my) for i in range(n_eff))
        sx = math.sqrt(sum((xs[i] - mx) ** 2 for i in range(n_eff)))
        sy = math.sqrt(sum((ys[i] - my) ** 2 for i in range(n_eff)))
        leads.append((k, cv / (sx * sy) if sx * sy > 0 else float("nan")))
    out.append("- lead-lag ρ:")
    for k, v in leads:
        out.append(f"    k={k:+d}: {v:+.4f}")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- F


def lens_f(prices: List[Dict], day: int) -> str:
    out = [f"### Day {day} — Lens F (weird)"]
    mids = [p["mid"] for p in prices if p.get("mid") is not None]
    if not mids:
        return out[0] + "\n— no data\n"
    # bimodality flag: histogram with 20 bins
    n_bins = 20
    lo, hi = min(mids), max(mids)
    if hi == lo:
        out.append("- single-valued mid")
        return "\n".join(out) + "\n"
    counts = [0] * n_bins
    for m in mids:
        b = min(n_bins - 1, int((m - lo) / (hi - lo) * n_bins))
        counts[b] += 1
    # naive bimodality: count peaks
    peaks = sum(1 for i in range(1, n_bins - 1) if counts[i] > counts[i - 1] and counts[i] > counts[i + 1])
    out.append(f"- mid histogram peaks ≥1: {peaks}")
    # ticks where book briefly empties
    no_bid = sum(1 for p in prices if p.get("b1") is None)
    no_ask = sum(1 for p in prices if p.get("a1") is None)
    out.append(f"- ticks no_bid={no_bid}, no_ask={no_ask}")
    # qty multiples-of-N
    bv1 = [p.get("bv1") for p in prices if p.get("bv1") is not None]
    av1 = [abs(p.get("av1")) for p in prices if p.get("av1") is not None]
    if bv1:
        unique_bv = len(set(int(x) for x in bv1))
        modes = sorted(((sum(1 for x in bv1 if int(x) == v), v) for v in set(int(x) for x in bv1)), reverse=True)[:3]
        out.append(f"- bv1 unique={unique_bv}, top modes (count, qty): {modes}")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- driver


def run_product(product: str, days: List[int]) -> None:
    print(f"# Lens battery — {product}\n")
    for d in days:
        prices = load_prices(product, d)
        trades = load_trades(product, d)
        print(f"## Day {d} ({len(prices)} snapshots, {len(trades)} trades)\n")
        print(lens_a(prices, product, d))
        print(lens_b(prices, d))
        print(lens_c(prices, d))
        print(lens_d(prices, trades, d))
        e = lens_e(prices, product, d)
        if e:
            print(e)
        print(lens_f(prices, d))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    prod = sys.argv[1]
    days = [int(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else [1, 2, 3]
    run_product(prod, days)
