#!/usr/bin/env python3
"""Targeted Ash analysis on two-sided book states only."""

import csv
import os
import math
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets", "round1")
DAYS = [-2, -1, 0]
ASH = "ASH_COATED_OSMIUM"


def load_prices(day):
    rows = []
    path = os.path.join(DATA_DIR, f"prices_round_1_day_{day}.csv")
    with open(path) as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            rows.append(row)
    return rows


def load_trades(day):
    rows = []
    path = os.path.join(DATA_DIR, f"trades_round_1_day_{day}.csv")
    with open(path) as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            rows.append(row)
    return rows


def parse_book(row):
    product = row["product"]
    ts = int(row["timestamp"])
    bids = []
    asks = []
    for i in range(1, 4):
        bp = row.get(f"bid_price_{i}", "")
        bv = row.get(f"bid_volume_{i}", "")
        if bp and bv:
            bids.append((int(bp), int(bv)))
        ap = row.get(f"ask_price_{i}", "")
        av = row.get(f"ask_volume_{i}", "")
        if ap and av:
            asks.append((int(ap), int(av)))
    bids.sort(key=lambda x: -x[0])
    asks.sort(key=lambda x: x[0])
    return {"product": product, "timestamp": ts, "bids": bids, "asks": asks}


print("=" * 80)
print("TARGETED ASH ANALYSIS (TWO-SIDED STATES ONLY)")
print("=" * 80)

# Build per-day series of two-sided Ash book states
for day in DAYS:
    prices = load_prices(day)
    trades_data = load_trades(day)
    ash_books = [parse_book(r) for r in prices if r["product"] == ASH]

    # Filter to two-sided only
    two_sided = [b for b in ash_books if b["bids"] and b["asks"]]
    total_books = len(ash_books)
    print(f"\nDay {day}: total={total_books}, two_sided={len(two_sided)}, one_sided={total_books - len(two_sided)}")

    series = []
    for b in two_sided:
        bb, bv = b["bids"][0]
        ba, av = b["asks"][0]
        mid = (bb + ba) / 2.0
        spread = ba - bb
        imbalance = (bv - av) / (bv + av) if (bv + av) > 0 else 0
        microprice = (bb * av + ba * bv) / (bv + av) if (bv + av) > 0 else mid

        # Compute mm10_mid
        bid10 = None
        for p, v in b["bids"]:
            if v >= 10:
                bid10 = p
                break
        ask10 = None
        for p, v in b["asks"]:
            if v >= 10:
                ask10 = p
                break
        mm10 = (bid10 + ask10) / 2.0 if bid10 is not None and ask10 is not None else mid

        # Full book volume
        total_bid_vol = sum(v for _, v in b["bids"])
        total_ask_vol = sum(v for _, v in b["asks"])
        full_imb = (total_bid_vol - total_ask_vol) / (total_bid_vol + total_ask_vol) if (total_bid_vol + total_ask_vol) > 0 else 0

        series.append({
            "ts": b["timestamp"], "mid": mid, "spread": spread,
            "imbalance": imbalance, "microprice": microprice,
            "mm10_mid": mm10, "full_imbalance": full_imb,
            "bb": bb, "ba": ba, "bv": bv, "av": av,
            "total_bid_vol": total_bid_vol, "total_ask_vol": total_ask_vol,
        })

    # Compute future returns at various horizons (two-sided to two-sided)
    for i in range(len(series)):
        for h in [1, 5, 10, 20, 50]:
            j = i + h
            if j < len(series):
                series[i][f"ret_{h}"] = series[j]["mid"] - series[i]["mid"]

    # ---- Analysis 1: Imbalance -> Future Return ----
    print(f"\n  --- Imbalance -> Future Return (two-sided only) ---")
    imb_buckets = defaultdict(lambda: defaultdict(list))
    for s in series:
        imb = s["imbalance"]
        bucket = round(imb * 5) / 5
        for h in [1, 5, 10, 20]:
            key = f"ret_{h}"
            if key in s:
                imb_buckets[bucket][h].append(s[key])

    print(f"  {'Imbalance':>12} {'n':>6} {'ret_1':>8} {'ret_5':>8} {'ret_10':>8} {'ret_20':>8}")
    for bucket in sorted(imb_buckets.keys()):
        n = len(imb_buckets[bucket].get(10, []))
        if n < 10:
            continue
        avgs = {}
        for h in [1, 5, 10, 20]:
            vals = imb_buckets[bucket].get(h, [])
            avgs[h] = sum(vals) / len(vals) if vals else 0
        print(f"  {bucket:>12.2f} {n:>6} {avgs[1]:>8.3f} {avgs[5]:>8.3f} {avgs[10]:>8.3f} {avgs[20]:>8.3f}")

    # ---- Analysis 2: (Microprice - Mid) as a signal ----
    print(f"\n  --- Microprice Bias -> Future Return ---")
    micro_buckets = defaultdict(lambda: defaultdict(list))
    for s in series:
        bias = s["microprice"] - s["mid"]
        bucket = round(bias * 2) / 2
        for h in [1, 5, 10, 20]:
            key = f"ret_{h}"
            if key in s:
                micro_buckets[bucket][h].append(s[key])

    print(f"  {'MicroBias':>12} {'n':>6} {'ret_1':>8} {'ret_5':>8} {'ret_10':>8} {'ret_20':>8}")
    for bucket in sorted(micro_buckets.keys()):
        n = len(micro_buckets[bucket].get(10, []))
        if n < 10:
            continue
        avgs = {}
        for h in [1, 5, 10, 20]:
            vals = micro_buckets[bucket].get(h, [])
            avgs[h] = sum(vals) / len(vals) if vals else 0
        print(f"  {bucket:>12.1f} {n:>6} {avgs[1]:>8.3f} {avgs[5]:>8.3f} {avgs[10]:>8.3f} {avgs[20]:>8.3f}")

    # ---- Analysis 3: Spread -> Future Return ----
    print(f"\n  --- Spread -> Future Return ---")
    spread_buckets = defaultdict(lambda: defaultdict(list))
    for s in series:
        for h in [1, 5, 10, 20]:
            key = f"ret_{h}"
            if key in s:
                spread_buckets[s["spread"]][h].append(s[key])

    print(f"  {'Spread':>8} {'n':>6} {'ret_1':>8} {'ret_5':>8} {'ret_10':>8} {'ret_20':>8} {'abs(ret_10)':>12}")
    for sp in sorted(spread_buckets.keys()):
        n = len(spread_buckets[sp].get(10, []))
        if n < 20:
            continue
        avgs = {}
        for h in [1, 5, 10, 20]:
            vals = spread_buckets[sp].get(h, [])
            avgs[h] = sum(vals) / len(vals) if vals else 0
        abs10 = sum(abs(v) for v in spread_buckets[sp].get(10, [])) / n
        print(f"  {sp:>8.0f} {n:>6} {avgs[1]:>8.3f} {avgs[5]:>8.3f} {avgs[10]:>8.3f} {avgs[20]:>8.3f} {abs10:>12.3f}")

    # ---- Analysis 4: Mid Deviation from Anchor -> Mean Reversion ----
    print(f"\n  --- Mid Deviation from 10000 -> Future Return ---")
    dev_buckets = defaultdict(lambda: defaultdict(list))
    for s in series:
        dev = s["mid"] - 10000.0
        bucket = round(dev)
        for h in [1, 5, 10, 20]:
            key = f"ret_{h}"
            if key in s:
                dev_buckets[bucket][h].append(s[key])

    print(f"  {'MidDev':>8} {'n':>6} {'ret_1':>8} {'ret_5':>8} {'ret_10':>8} {'ret_20':>8}")
    for bucket in sorted(dev_buckets.keys()):
        n = len(dev_buckets[bucket].get(10, []))
        if n < 20:
            continue
        avgs = {}
        for h in [1, 5, 10, 20]:
            vals = dev_buckets[bucket].get(h, [])
            avgs[h] = sum(vals) / len(vals) if vals else 0
        print(f"  {bucket:>8.0f} {n:>6} {avgs[1]:>8.3f} {avgs[5]:>8.3f} {avgs[10]:>8.3f} {avgs[20]:>8.3f}")

    # ---- Analysis 5: Taking opportunity analysis ----
    print(f"\n  --- Taking Opportunities (distance from fair) ---")
    fair_anchor = 10000.0
    for edge in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        buy_opps = 0
        buy_pnl = []
        sell_opps = 0
        sell_pnl = []
        for i, s in enumerate(series):
            fair = fair_anchor + 0.65 * max(-3, min(3, s["mm10_mid"] - fair_anchor)) + 0.25 * max(-1.5, min(1.5, s["microprice"] - s["mid"]))
            if s["ba"] <= fair - edge:
                buy_opps += 1
                if i + 10 < len(series):
                    buy_pnl.append(series[i+10]["mid"] - s["ba"])
            if s["bb"] >= fair + edge:
                sell_opps += 1
                if i + 10 < len(series):
                    sell_pnl.append(s["bb"] - series[i+10]["mid"])
        all_pnl = buy_pnl + sell_pnl
        avg_pnl = sum(all_pnl) / len(all_pnl) if all_pnl else 0
        n_total = buy_opps + sell_opps
        win = sum(1 for p in all_pnl if p > 0) / len(all_pnl) * 100 if all_pnl else 0
        print(f"  Edge {edge:.1f}: n_opps={n_total:>5} (buy={buy_opps}, sell={sell_opps}), avg_pnl={avg_pnl:>7.2f}, win={win:.0f}%")

    # ---- Analysis 6: What fair value estimator is best? ----
    print(f"\n  --- Fair Value Estimator Comparison (h=10 MAE) ---")
    estimators = {
        "simple_mid": lambda s: s["mid"],
        "mm10_mid": lambda s: s["mm10_mid"],
        "microprice": lambda s: s["microprice"],
        "anchor_10000": lambda s: 10000.0,
        "v6_fair": lambda s: 10000.0 + 0.65 * max(-3, min(3, s["mm10_mid"] - 10000.0)) + 0.25 * max(-1.5, min(1.5, s["microprice"] - s["mid"])),
        "anchor+imb": lambda s: 10000.0 + 0.65 * max(-3, min(3, s["mm10_mid"] - 10000.0)) + 0.50 * max(-2.0, min(2.0, s["microprice"] - s["mid"])),
        "anchor+imb+full": lambda s: 10000.0 + 0.65 * max(-3, min(3, s["mm10_mid"] - 10000.0)) + 0.50 * max(-2.0, min(2.0, s["microprice"] - s["mid"])) + 0.30 * max(-2, min(2, s["full_imbalance"] * 3)),
    }
    for name, fn in estimators.items():
        maes = []
        for i, s in enumerate(series):
            if i + 10 >= len(series):
                break
            fair = fn(s)
            actual = series[i + 10]["mid"]
            maes.append(abs(actual - fair))
        avg_mae = sum(maes) / len(maes) if maes else 0
        print(f"  {name:>20}: MAE(h=10) = {avg_mae:.4f}")

    # ---- Analysis 7: Combined signal (imbalance + microprice) ----
    print(f"\n  --- Combined Signal: Imbalance + Microprice Bias ---")
    for imb_threshold in [0.15, 0.25, 0.35]:
        strong_buy = []
        strong_sell = []
        for i, s in enumerate(series):
            if f"ret_10" not in s:
                continue
            micro_bias = s["microprice"] - s["mid"]
            imb = s["imbalance"]
            if imb > imb_threshold and micro_bias > 0.5:
                strong_buy.append(s["ret_10"])
            elif imb < -imb_threshold and micro_bias < -0.5:
                strong_sell.append(s["ret_10"])

        if strong_buy:
            print(f"  imb>{imb_threshold}, micro>0.5: n={len(strong_buy)}, avg_ret10={sum(strong_buy)/len(strong_buy):.3f}")
        if strong_sell:
            print(f"  imb<-{imb_threshold}, micro<-0.5: n={len(strong_sell)}, avg_ret10={sum(strong_sell)/len(strong_sell):.3f}")

# ---- Analysis 8: Ash market trade flow analysis ----
print("\n" + "=" * 80)
print("ASH MARKET TRADE FLOW SIGNAL (ALL DAYS)")
print("=" * 80)

for day in DAYS:
    prices = load_prices(day)
    trades_data = load_trades(day)
    ash_books = [parse_book(r) for r in prices if r["product"] == ASH]
    ash_trades = [t for t in trades_data if t["symbol"] == ASH]

    two_sided = [b for b in ash_books if b["bids"] and b["asks"]]
    series = []
    for b in two_sided:
        bb, bv = b["bids"][0]
        ba, av = b["asks"][0]
        mid = (bb + ba) / 2.0
        series.append({"ts": b["timestamp"], "mid": mid, "bb": bb, "ba": ba})

    ts_to_idx = {s["ts"]: i for i, s in enumerate(series)}

    # Build flow EMA
    trade_by_ts = defaultdict(int)
    for t in ash_trades:
        ts = int(t["timestamp"])
        price = float(t["price"])
        qty = int(t["quantity"])
        nearest_ts = min(ts_to_idx.keys(), key=lambda x: abs(x - ts))
        nearest_mid = series[ts_to_idx[nearest_ts]]["mid"]
        if price > nearest_mid:
            trade_by_ts[nearest_ts] += qty
        else:
            trade_by_ts[nearest_ts] -= qty

    flow_ema = 0
    for i, s in enumerate(series):
        flow_now = trade_by_ts.get(s["ts"], 0)
        flow_ema = 0.86 * flow_ema + flow_now
        s["flow_ema"] = flow_ema

    # Bucket flow EMA and check future returns
    for i in range(len(series)):
        for h in [1, 5, 10, 20]:
            j = i + h
            if j < len(series):
                series[i][f"ret_{h}"] = series[j]["mid"] - series[i]["mid"]

    flow_buckets = defaultdict(lambda: defaultdict(list))
    for s in series:
        fe = s["flow_ema"]
        if fe > 6:
            bucket = "strong_pos"
        elif fe > 3:
            bucket = "pos"
        elif fe < -6:
            bucket = "strong_neg"
        elif fe < -3:
            bucket = "neg"
        else:
            bucket = "neutral"
        for h in [1, 5, 10, 20]:
            key = f"ret_{h}"
            if key in s:
                flow_buckets[bucket][h].append(s[key])

    print(f"\nDay {day}:")
    for bucket in ["strong_neg", "neg", "neutral", "pos", "strong_pos"]:
        n = len(flow_buckets[bucket].get(10, []))
        if n == 0:
            continue
        avgs = {}
        for h in [1, 5, 10, 20]:
            vals = flow_buckets[bucket].get(h, [])
            avgs[h] = sum(vals) / len(vals) if vals else 0
        print(f"  {bucket:>12}: n={n:>5}, ret_1={avgs[1]:>7.3f}, ret_5={avgs[5]:>7.3f}, ret_10={avgs[10]:>7.3f}, ret_20={avgs[20]:>7.3f}")


# ---- Analysis 9: Ash quote tightness sensitivity ----
print("\n" + "=" * 80)
print("ASH QUOTE TIGHTNESS SENSITIVITY")
print("=" * 80)

for day in DAYS:
    prices = load_prices(day)
    ash_books = [parse_book(r) for r in prices if r["product"] == ASH]
    two_sided = [b for b in ash_books if b["bids"] and b["asks"]]

    spreads = [b["asks"][0][0] - b["bids"][0][0] for b in two_sided]
    mids = [(b["bids"][0][0] + b["asks"][0][0]) / 2.0 for b in two_sided]

    avg_spread = sum(spreads) / len(spreads)
    median_spread = sorted(spreads)[len(spreads)//2]

    # How often is the spread narrow enough to improve on?
    narrow = sum(1 for s in spreads if s <= 14)
    wide = sum(1 for s in spreads if s >= 18)

    print(f"\nDay {day}: avg_spread={avg_spread:.1f}, median={median_spread}, narrow(<=14)={narrow} ({narrow/len(spreads)*100:.1f}%), wide(>=18)={wide} ({wide/len(spreads)*100:.1f}%)")

    # When spread is narrow, what happens?
    narrow_rets = []
    normal_rets = []
    wide_rets = []
    for i, b in enumerate(two_sided):
        sp = b["asks"][0][0] - b["bids"][0][0]
        mid = (b["bids"][0][0] + b["asks"][0][0]) / 2.0
        if i + 10 < len(two_sided):
            ret = (two_sided[i+10]["bids"][0][0] + two_sided[i+10]["asks"][0][0]) / 2.0 - mid
            if sp <= 14:
                narrow_rets.append(ret)
            elif sp >= 18:
                wide_rets.append(ret)
            else:
                normal_rets.append(ret)

    for name, rets in [("narrow<=14", narrow_rets), ("normal 15-17", normal_rets), ("wide>=18", wide_rets)]:
        if rets:
            avg = sum(rets) / len(rets)
            std = math.sqrt(sum((r - avg)**2 for r in rets) / len(rets))
            absavg = sum(abs(r) for r in rets) / len(rets)
            print(f"  {name}: n={len(rets)}, avg_ret10={avg:.3f}, std={std:.3f}, avg_abs_ret10={absavg:.3f}")

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
