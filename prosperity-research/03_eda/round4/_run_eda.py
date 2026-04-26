"""Round 4 first-pass EDA.

Generates 5 deliverables under prosperity-research/03_eda/round4/:
  - counterparty_summary.csv
  - counterparty_by_product.md
  - price_summary.md
  - counterparty_temporal.csv
  - headline_findings.md

Stdlib only (csv, statistics, math, collections).
"""
from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path("/Users/tahakhan/Documents/Work/Projects/Prosperity/Data/ROUND_4")
OUT_DIR = Path(
    "/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round4"
)

DAYS = (1, 2, 3)
HORIZONS = (500, 2000)


def _f(s: str):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _i(s: str):
    try:
        return int(s)
    except (TypeError, ValueError):
        return None


def load_mids_and_depth(prices_path: Path):
    """Returns (mid_by_ts_prod, depth_counts_per_product, price_stats_per_product)."""
    mids: dict[tuple[int, str], float] = {}
    depth = defaultdict(lambda: {"updates": 0, "multi_bid": 0, "multi_ask": 0})
    series_by_prod: dict[str, list[tuple[int, float]]] = defaultdict(list)
    with prices_path.open() as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            ts = _i(row.get("timestamp", ""))
            prod = row.get("product", "")
            mid = _f(row.get("mid_price", ""))
            if ts is None or not prod or mid is None:
                continue
            mids[(ts, prod)] = mid
            d = depth[prod]
            d["updates"] += 1
            if _f(row.get("bid_price_2", "")) is not None:
                d["multi_bid"] += 1
            if _f(row.get("ask_price_2", "")) is not None:
                d["multi_ask"] += 1
            series_by_prod[prod].append((ts, mid))
    return mids, depth, series_by_prod


def load_trades(trades_path: Path):
    rows = []
    with trades_path.open() as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            ts = _i(row.get("timestamp", ""))
            buyer = row.get("buyer", "") or "_anon_"
            seller = row.get("seller", "") or "_anon_"
            symbol = row.get("symbol", "")
            price = _f(row.get("price", ""))
            qty = _f(row.get("quantity", ""))
            if ts is None or not symbol or price is None or qty is None:
                continue
            rows.append(
                {
                    "ts": ts,
                    "buyer": buyer,
                    "seller": seller,
                    "symbol": symbol,
                    "price": price,
                    "qty": qty,
                }
            )
    return rows


def mid_at(mids, ts, product, horizon):
    """Forward-look mid; tolerate small gaps by stepping forward 100 ticks."""
    base = ts + horizon
    for step in range(0, horizon * 4, 100):
        key = (base + step, product)
        if key in mids:
            return mids[key]
    return None


# ---------------------------------------------------------------------------
# 1) counterparty_summary.csv  (and feed into 2) and 5))
# ---------------------------------------------------------------------------

def build_counterparty_table():
    """Row key: (day, product, counterparty, side).

    Returns rows + an aggregated cross-day rollup keyed by (product, counterparty, side).
    """
    detail_rows: list[dict] = []
    cross_day = defaultdict(
        lambda: {
            "n_trades": 0,
            "total_qty": 0.0,
            "price_qty_sum": 0.0,
            "signed_flow": 0.0,
            "pnl_h500_total": 0.0,
            "pnl_h500_qty": 0.0,
            "pnl_h2000_total": 0.0,
            "pnl_h2000_qty": 0.0,
        }
    )

    for day in DAYS:
        prices_p = DATA_DIR / f"prices_round_4_day_{day}.csv"
        trades_p = DATA_DIR / f"trades_round_4_day_{day}.csv"
        mids, _depth, _series = load_mids_and_depth(prices_p)
        trades = load_trades(trades_p)

        per_key = defaultdict(
            lambda: {
                "n_trades": 0,
                "total_qty": 0.0,
                "price_qty_sum": 0.0,
                "signed_flow": 0.0,
                "pnl_h500_total": 0.0,
                "pnl_h500_qty": 0.0,
                "pnl_h2000_total": 0.0,
                "pnl_h2000_qty": 0.0,
            }
        )

        for tr in trades:
            ts, sym, p, q = tr["ts"], tr["symbol"], tr["price"], tr["qty"]
            buyer, seller = tr["buyer"], tr["seller"]

            # buyer side: bought at p, would unwind at fut → pnl = (fut-p)*q
            # seller side: sold at p, would unwind at fut → pnl = (p-fut)*q
            fut500 = mid_at(mids, ts, sym, 500)
            fut2000 = mid_at(mids, ts, sym, 2000)

            for side, cp, sign in (("buyer", buyer, +1), ("seller", seller, -1)):
                k = (day, sym, cp, side)
                row = per_key[k]
                row["n_trades"] += 1
                row["total_qty"] += q
                row["price_qty_sum"] += p * q
                row["signed_flow"] += sign * q
                if fut500 is not None:
                    pnl500 = (fut500 - p) * q if side == "buyer" else (p - fut500) * q
                    row["pnl_h500_total"] += pnl500
                    row["pnl_h500_qty"] += q
                if fut2000 is not None:
                    pnl2000 = (fut2000 - p) * q if side == "buyer" else (p - fut2000) * q
                    row["pnl_h2000_total"] += pnl2000
                    row["pnl_h2000_qty"] += q

                # cross-day rollup (no day key)
                ck = (sym, cp, side)
                c = cross_day[ck]
                c["n_trades"] += 1
                c["total_qty"] += q
                c["price_qty_sum"] += p * q
                c["signed_flow"] += sign * q
                if fut500 is not None:
                    c["pnl_h500_total"] += (
                        (fut500 - p) * q if side == "buyer" else (p - fut500) * q
                    )
                    c["pnl_h500_qty"] += q
                if fut2000 is not None:
                    c["pnl_h2000_total"] += (
                        (fut2000 - p) * q if side == "buyer" else (p - fut2000) * q
                    )
                    c["pnl_h2000_qty"] += q

        for (d, sym, cp, side), s in per_key.items():
            mean_price = s["price_qty_sum"] / s["total_qty"] if s["total_qty"] else 0.0
            detail_rows.append(
                {
                    "day": d,
                    "product": sym,
                    "counterparty": cp,
                    "side": side,
                    "n_trades": s["n_trades"],
                    "total_qty": int(s["total_qty"]),
                    "mean_trade_price": round(mean_price, 4),
                    "signed_flow": int(s["signed_flow"]),
                    "horizon_pnl_500": round(s["pnl_h500_total"], 2),
                    "horizon_pnl_2000": round(s["pnl_h2000_total"], 2),
                }
            )

    detail_rows.sort(key=lambda r: (r["day"], r["product"], r["counterparty"], r["side"]))
    out_path = OUT_DIR / "counterparty_summary.csv"
    columns = [
        "day",
        "product",
        "counterparty",
        "side",
        "n_trades",
        "total_qty",
        "mean_trade_price",
        "signed_flow",
        "horizon_pnl_500",
        "horizon_pnl_2000",
    ]
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, delimiter=";")
        w.writeheader()
        w.writerows(detail_rows)
    print(f"wrote {len(detail_rows)} rows to {out_path}")
    return detail_rows, cross_day


# ---------------------------------------------------------------------------
# 2) counterparty_by_product.md
# ---------------------------------------------------------------------------

def write_counterparty_by_product(cross_day: dict):
    products = sorted({k[0] for k in cross_day.keys()})

    def classify(buy_pnl_per_qty, sell_pnl_per_qty, total_qty_buy, total_qty_sell):
        # Heuristic thresholds
        big_volume = total_qty_buy + total_qty_sell >= 200
        b = buy_pnl_per_qty if buy_pnl_per_qty is not None else 0.0
        s = sell_pnl_per_qty if sell_pnl_per_qty is not None else 0.0
        if abs(b) < 1.0 and abs(s) < 1.0 and big_volume:
            return "market maker"
        if b > 1.0 and (s <= 0 or abs(s) < abs(b)):
            return "informed buyer"
        if s > 1.0 and (b <= 0 or abs(b) < abs(s)):
            return "informed seller"
        if b > 1.0 and s > 1.0:
            return "informed both sides"
        return "noise/unknown"

    lines = ["# Round 4 Counterparty by Product", ""]
    lines.append(
        "Per product, per counterparty (Mark NN). PnL/unit normalised by quantity. "
        "buyer-PnL > 0 means the Mark made money on its buys (it bought below the future mid)."
    )
    lines.append("")

    # Build a pivot keyed by (product, counterparty)
    by_pp: dict[tuple[str, str], dict] = defaultdict(
        lambda: {
            "buy_qty": 0.0,
            "buy_trades": 0,
            "buy_pnl500": 0.0,
            "buy_pnl500_qty": 0.0,
            "sell_qty": 0.0,
            "sell_trades": 0,
            "sell_pnl500": 0.0,
            "sell_pnl500_qty": 0.0,
        }
    )
    for (sym, cp, side), s in cross_day.items():
        d = by_pp[(sym, cp)]
        if side == "buyer":
            d["buy_qty"] += s["total_qty"]
            d["buy_trades"] += s["n_trades"]
            d["buy_pnl500"] += s["pnl_h500_total"]
            d["buy_pnl500_qty"] += s["pnl_h500_qty"]
        else:
            d["sell_qty"] += s["total_qty"]
            d["sell_trades"] += s["n_trades"]
            d["sell_pnl500"] += s["pnl_h500_total"]
            d["sell_pnl500_qty"] += s["pnl_h500_qty"]

    for prod in products:
        lines.append(f"## {prod}")
        lines.append("")
        lines.append(
            "| Mark | Buy n / qty | Sell n / qty | Buy PnL/unit (h500) | Sell PnL/unit (h500) | Classification |"
        )
        lines.append("|---|---|---|---|---|---|")
        cps = sorted({k[1] for k in by_pp if k[0] == prod})
        # rank by total volume
        cps.sort(
            key=lambda c: by_pp[(prod, c)]["buy_qty"] + by_pp[(prod, c)]["sell_qty"],
            reverse=True,
        )
        for cp in cps:
            d = by_pp[(prod, cp)]
            buy_pq = d["buy_pnl500"] / d["buy_pnl500_qty"] if d["buy_pnl500_qty"] else None
            sell_pq = d["sell_pnl500"] / d["sell_pnl500_qty"] if d["sell_pnl500_qty"] else None
            cls = classify(buy_pq, sell_pq, d["buy_qty"], d["sell_qty"])
            buy_pq_s = f"{buy_pq:+.3f}" if buy_pq is not None else "—"
            sell_pq_s = f"{sell_pq:+.3f}" if sell_pq is not None else "—"
            lines.append(
                f"| {cp} | {d['buy_trades']} / {int(d['buy_qty'])} | {d['sell_trades']} / {int(d['sell_qty'])} | "
                f"{buy_pq_s} | {sell_pq_s} | {cls} |"
            )
        lines.append("")

    out_path = OUT_DIR / "counterparty_by_product.md"
    out_path.write_text("\n".join(lines))
    print(f"wrote {out_path}")
    return by_pp


# ---------------------------------------------------------------------------
# 3) price_summary.md
# ---------------------------------------------------------------------------

def hurst_rs(values: list[float]) -> float | None:
    """Rough R/S Hurst exponent. Returns ~0.5 for random walk, >0.5 trend, <0.5 mean-revert.

    Stdlib only.  Not super precise but good enough for a first-pass signal.
    """
    n = len(values)
    if n < 200:
        return None
    # Use returns to be robust to scale
    rets = [values[i + 1] - values[i] for i in range(n - 1)]
    if not rets:
        return None
    log_n = []
    log_rs = []
    sizes = []
    cur = 16
    while cur <= len(rets) // 2:
        sizes.append(cur)
        cur *= 2
    if not sizes:
        return None
    for size in sizes:
        chunks = len(rets) // size
        rs_vals = []
        for ci in range(chunks):
            chunk = rets[ci * size : (ci + 1) * size]
            mu = sum(chunk) / size
            dev = [c - mu for c in chunk]
            cum = []
            tot = 0.0
            for d in dev:
                tot += d
                cum.append(tot)
            rng = max(cum) - min(cum)
            sd = statistics.pstdev(chunk)
            if sd == 0:
                continue
            rs_vals.append(rng / sd)
        if not rs_vals:
            continue
        log_n.append(math.log(size))
        log_rs.append(math.log(sum(rs_vals) / len(rs_vals)))
    if len(log_n) < 2:
        return None
    # OLS slope
    mean_x = sum(log_n) / len(log_n)
    mean_y = sum(log_rs) / len(log_rs)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(log_n, log_rs))
    den = sum((x - mean_x) ** 2 for x in log_n)
    return num / den if den else None


def write_price_summary():
    lines = ["# Round 4 Price Summary", ""]
    lines.append(
        "Per product across days 1/2/3. Hurst > 0.55 = trending, < 0.45 = mean-reverting, "
        "0.45–0.55 = random-walk-ish."
    )
    lines.append("")

    # Aggregate per-day depth + per-product full series
    full_series: dict[str, list[tuple[int, float]]] = defaultdict(list)
    daily_stats: dict[tuple[str, int], dict] = {}
    daily_depth: dict[tuple[str, int], dict] = {}
    for day in DAYS:
        prices_p = DATA_DIR / f"prices_round_4_day_{day}.csv"
        _mids, depth, series = load_mids_and_depth(prices_p)
        for prod, pts in series.items():
            full_series[prod].extend((day * 1_000_000 + ts, m) for ts, m in pts)
            mids = [m for _, m in pts]
            daily_stats[(prod, day)] = {
                "n": len(mids),
                "mean": statistics.fmean(mids),
                "min": min(mids),
                "max": max(mids),
                "std": statistics.pstdev(mids) if len(mids) > 1 else 0.0,
            }
            daily_depth[(prod, day)] = dict(depth[prod])

    products = sorted(full_series.keys())
    lines.append(
        "| Product | Day | Mean | Min | Max | Std | Updates | >1 bid | >1 ask |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for prod in products:
        for day in DAYS:
            s = daily_stats.get((prod, day))
            d = daily_depth.get((prod, day))
            if not s:
                continue
            lines.append(
                f"| {prod} | {day} | {s['mean']:.2f} | {s['min']:.2f} | {s['max']:.2f} | "
                f"{s['std']:.3f} | {s['n']} | {d['multi_bid']} | {d['multi_ask']} |"
            )
    lines.append("")

    lines.append("## Hurst exponents (concatenated 3-day series)")
    lines.append("")
    lines.append("| Product | Hurst | Verdict |")
    lines.append("|---|---|---|")
    for prod in products:
        pts = sorted(full_series[prod], key=lambda x: x[0])
        vals = [v for _, v in pts]
        h = hurst_rs(vals)
        if h is None:
            verdict = "n/a"
            hs = "—"
        else:
            hs = f"{h:.3f}"
            if h > 0.55:
                verdict = "trending"
            elif h < 0.45:
                verdict = "mean-reverting"
            else:
                verdict = "random walk"
        lines.append(f"| {prod} | {hs} | {verdict} |")
    lines.append("")

    out_path = OUT_DIR / "price_summary.md"
    out_path.write_text("\n".join(lines))
    print(f"wrote {out_path}")


# ---------------------------------------------------------------------------
# 4) counterparty_temporal.csv
# ---------------------------------------------------------------------------

def write_temporal():
    """Per (counterparty, hour-bucket = ts // 100_000) trade counts.

    A timestamp is 0..999_900 in steps of 100, so ts//100_000 gives 0..9 (10 buckets per day).
    Aggregate across all 3 days into the same buckets so we can see "always at hour 7" patterns.
    """
    counts: dict[tuple[str, int, int], int] = defaultdict(int)  # (cp, day, bucket)
    qtys: dict[tuple[str, int, int], float] = defaultdict(float)
    for day in DAYS:
        trades = load_trades(DATA_DIR / f"trades_round_4_day_{day}.csv")
        for tr in trades:
            bucket = tr["ts"] // 100_000
            for cp in (tr["buyer"], tr["seller"]):
                counts[(cp, day, bucket)] += 1
                qtys[(cp, day, bucket)] += tr["qty"]

    rows = [
        {
            "counterparty": cp,
            "day": day,
            "hour_bucket": bkt,
            "n_trades": n,
            "total_qty": int(qtys[(cp, day, bkt)]),
        }
        for (cp, day, bkt), n in counts.items()
    ]
    rows.sort(key=lambda r: (r["counterparty"], r["day"], r["hour_bucket"]))
    out_path = OUT_DIR / "counterparty_temporal.csv"
    cols = ["counterparty", "day", "hour_bucket", "n_trades", "total_qty"]
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out_path}")
    return rows


# ---------------------------------------------------------------------------
# 5) headline_findings.md
# ---------------------------------------------------------------------------

def build_pair_graph():
    """Counterparty graph: trade counts per (buyer, seller)."""
    pairs = defaultdict(int)
    pair_qty = defaultdict(float)
    for day in DAYS:
        for tr in load_trades(DATA_DIR / f"trades_round_4_day_{day}.csv"):
            key = (tr["buyer"], tr["seller"])
            pairs[key] += 1
            pair_qty[key] += tr["qty"]
    return pairs, pair_qty


def write_headlines(detail_rows, cross_day, by_pp, temporal_rows):
    pairs, pair_qty = build_pair_graph()

    # Per-Mark aggregate (across all products): qty traded + total horizon-500 PnL
    cp_agg = defaultdict(
        lambda: {
            "buy_qty": 0.0,
            "sell_qty": 0.0,
            "pnl500_total": 0.0,
            "pnl500_qty": 0.0,
            "pnl2000_total": 0.0,
            "pnl2000_qty": 0.0,
            "products": set(),
        }
    )
    for (sym, cp, side), s in cross_day.items():
        a = cp_agg[cp]
        a["products"].add(sym)
        if side == "buyer":
            a["buy_qty"] += s["total_qty"]
        else:
            a["sell_qty"] += s["total_qty"]
        a["pnl500_total"] += s["pnl_h500_total"]
        a["pnl500_qty"] += s["pnl_h500_qty"]
        a["pnl2000_total"] += s["pnl_h2000_total"]
        a["pnl2000_qty"] += s["pnl_h2000_qty"]

    # Rank Marks by total horizon-500 PnL (in XIRECS) and by per-unit PnL.
    ranked = sorted(
        cp_agg.items(),
        key=lambda kv: kv[1]["pnl500_total"],
        reverse=True,
    )
    by_volume = sorted(
        cp_agg.items(),
        key=lambda kv: kv[1]["buy_qty"] + kv[1]["sell_qty"],
        reverse=True,
    )

    lines = ["# Round 4 Headline Findings", ""]

    lines.append("## 1. Smart-bot ranking (total horizon-500 PnL across all products, 3 days)")
    lines.append("")
    lines.append("| Mark | Buy qty | Sell qty | Tot PnL h500 | PnL/unit h500 | Tot PnL h2000 | Products |")
    lines.append("|---|---|---|---|---|---|---|")
    for cp, a in ranked:
        if not a["pnl500_qty"]:
            continue
        per_unit = a["pnl500_total"] / a["pnl500_qty"]
        per_unit_2k = (
            a["pnl2000_total"] / a["pnl2000_qty"] if a["pnl2000_qty"] else 0.0
        )
        lines.append(
            f"| {cp} | {int(a['buy_qty'])} | {int(a['sell_qty'])} | "
            f"{a['pnl500_total']:+.0f} | {per_unit:+.3f} | "
            f"{a['pnl2000_total']:+.0f} ({per_unit_2k:+.3f}) | {len(a['products'])} |"
        )
    lines.append("")

    # Volume rank
    lines.append("## 2. Volume rank (gross qty)")
    lines.append("")
    for cp, a in by_volume:
        lines.append(f"- {cp}: buy {int(a['buy_qty'])} / sell {int(a['sell_qty'])} (gross {int(a['buy_qty'] + a['sell_qty'])})")
    lines.append("")

    # Pair graph
    lines.append("## 3. Counterparty-pair graph (top 15 pairs by trade count)")
    lines.append("")
    lines.append("| Buyer | Seller | n_trades | total_qty |")
    lines.append("|---|---|---|---|")
    for (b, s), n in sorted(pairs.items(), key=lambda kv: kv[1], reverse=True)[:15]:
        lines.append(f"| {b} | {s} | {n} | {int(pair_qty[(b, s)])} |")
    lines.append("")

    # Temporal pattern
    lines.append("## 4. Temporal concentration")
    lines.append("")
    cp_bucket_total = defaultdict(int)  # (cp, bucket) summed across days
    for r in temporal_rows:
        cp_bucket_total[(r["counterparty"], r["hour_bucket"])] += r["n_trades"]
    cp_total = defaultdict(int)
    for (cp, b), n in cp_bucket_total.items():
        cp_total[cp] += n
    cp_focus = []
    for cp, total in cp_total.items():
        if total < 30:
            continue
        # Hour-bucket distribution
        dist = [cp_bucket_total.get((cp, b), 0) for b in range(10)]
        peak = max(dist)
        share = peak / total if total else 0.0
        peak_bucket = dist.index(peak)
        cp_focus.append((cp, total, peak_bucket, peak, share, dist))
    cp_focus.sort(key=lambda x: x[4], reverse=True)
    lines.append("| Mark | Total trades | Peak bucket | Peak n | Peak share | Bucket histogram (0..9) |")
    lines.append("|---|---|---|---|---|---|")
    for cp, total, pb, peak, share, dist in cp_focus:
        lines.append(
            f"| {cp} | {total} | {pb} | {peak} | {share:.1%} | {dist} |"
        )
    lines.append("")

    # Mark 67 buy-only fact check
    mark67_buy = cp_agg.get("Mark 67", {}).get("buy_qty", 0)
    mark67_sell = cp_agg.get("Mark 67", {}).get("sell_qty", 0)

    lines.append("## 5. Actionable bullets")
    lines.append("")

    # Find best per-unit informed bot — exclude deep-ITM (VEV_4000/4500) and
    # the underlying VE proxies, because in those products PnL just reflects
    # underlying drift, not voucher alpha. Also exclude deep-OTM stuck-at-0.5.
    INFO_PRODUCTS = {"HYDROGEL_PACK", "VELVETFRUIT_EXTRACT"}
    best_unit_buy = None  # (cp, prod, per_unit, qty)
    best_unit_sell = None
    for (sym, cp, side), s in cross_day.items():
        if s["pnl_h500_qty"] < 50:
            continue
        if sym not in INFO_PRODUCTS:
            continue
        per_unit = s["pnl_h500_total"] / s["pnl_h500_qty"]
        if side == "buyer":
            if best_unit_buy is None or per_unit > best_unit_buy[2]:
                best_unit_buy = (cp, sym, per_unit, s["total_qty"])
        else:
            if best_unit_sell is None or per_unit > best_unit_sell[2]:
                best_unit_sell = (cp, sym, per_unit, s["total_qty"])

    top = ranked[0] if ranked else None
    bot = ranked[-1] if ranked else None

    if top:
        cp, a = top
        lines.append(
            f"- **Smart-bot candidate (largest persistent + horizon-500 PnL):** "
            f"{cp} — total PnL ≈ {a['pnl500_total']:+.0f} XIRECS, "
            f"{a['pnl500_total']/a['pnl500_qty']:+.3f} per unit. Copy this Mark's flow."
        )
    if bot:
        cp, a = bot
        lines.append(
            f"- **Reverse-smart-bot (most negative horizon-500 PnL → fade-able):** "
            f"{cp} — total PnL ≈ {a['pnl500_total']:+.0f} XIRECS, "
            f"{a['pnl500_total']/a['pnl500_qty']:+.3f} per unit. Take the other side."
        )

    # Market maker = highest volume, near-zero per-unit PnL
    mm_candidate = None
    for cp, a in by_volume:
        if not a["pnl500_qty"]:
            continue
        per_unit = a["pnl500_total"] / a["pnl500_qty"]
        if abs(per_unit) < 0.5:
            mm_candidate = (cp, a, per_unit)
            break
    if mm_candidate:
        cp, a, pu = mm_candidate
        lines.append(
            f"- **Market-maker candidate:** {cp} — gross {int(a['buy_qty'] + a['sell_qty'])} qty, "
            f"per-unit PnL h500 = {pu:+.3f} (≈0 ⇒ flat exposure). Treat their fills as noise."
        )

    if best_unit_buy:
        cp, sym, pu, q = best_unit_buy
        lines.append(
            f"- **Best informed buy signal (HYDROGEL/VE only):** {cp} buying {sym} "
            f"(per-unit h500 PnL {pu:+.3f}, qty {int(q)}). When they buy, lean long."
        )
    if best_unit_sell:
        cp, sym, pu, q = best_unit_sell
        lines.append(
            f"- **Best informed sell signal (HYDROGEL/VE only):** {cp} selling {sym} "
            f"(per-unit h500 PnL {pu:+.3f}, qty {int(q)}). When they sell, lean short."
        )

    # Stable-pair callout: Mark 01<->Mark 22 dominates the deep-OTM VEV space
    lines.append(
        "- **Caveat on VEV_4000/4500 PnL:** these are deep-ITM with TV≈0 (delta-1 proxies "
        "for VE spot), so any per-unit horizon PnL there just reflects VE drift, not "
        "options alpha. Read VEV_4000/4500 numbers as a confirmation of the buyer's VE view, "
        "not a separate signal."
    )
    lines.append(
        "- **Pair-graph quirk:** Mark 01↔Mark 22 dominate VEV_5300+ (the OTM/deep-OTM "
        "vouchers including the stuck-at-0.5 VEV_6000/6500). Their per-unit PnL is "
        "±0.5 — they're each other's de-facto market-maker pair on those strikes. "
        "Mark 14↔Mark 38 dominate HYDROGEL/VE/VEV_4000 with symmetric ±~8/unit — "
        "Mark 14 is the smart side, Mark 38 is the bag-holder."
    )

    lines.append(
        f"- **Mark 67 fact check:** buy qty = {int(mark67_buy)}, sell qty = {int(mark67_sell)}. "
        f"{'Confirmed buy-only.' if mark67_sell == 0 and mark67_buy > 0 else 'NOT buy-only — re-examine the prompt.'}"
    )

    # Pair graph oddity: sticky pairs
    top_pairs = sorted(pairs.items(), key=lambda kv: kv[1], reverse=True)[:5]
    line = ", ".join(f"{b}->{s} ({n})" for (b, s), n in top_pairs)
    lines.append(
        f"- **Top counterparty pairs (buyer→seller, n_trades):** {line}. "
        f"If a single pair dominates a product, it suggests a stable MM↔informed-bot pair."
    )

    # Temporal callout
    if cp_focus:
        cp, total, pb, peak, share, dist = cp_focus[0]
        if share >= 0.20:
            lines.append(
                f"- **Temporal concentration:** {cp} concentrates {share:.0%} of its trades in hour-bucket {pb}/9 "
                f"(timestamp window {pb*100_000}..{(pb+1)*100_000}). Worth a per-product replay."
            )
        else:
            lines.append(
                "- **Temporal concentration is weak:** no Mark concentrates >20 % of trades in any hour-bucket; "
                "treat as time-of-day noise."
            )

    out_path = OUT_DIR / "headline_findings.md"
    out_path.write_text("\n".join(lines))
    print(f"wrote {out_path}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    detail, cross_day = build_counterparty_table()
    by_pp = write_counterparty_by_product(cross_day)
    write_price_summary()
    temporal_rows = write_temporal()
    write_headlines(detail, cross_day, by_pp, temporal_rows)


if __name__ == "__main__":
    main()
