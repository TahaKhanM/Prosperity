#!/usr/bin/env python3
"""Deep independent data analysis for Round 1 strategy improvement."""

import csv
import os
import math
import json
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets", "round1")
DAYS = [-2, -1, 0]
ASH = "ASH_COATED_OSMIUM"
PEPPER = "INTARIAN_PEPPER_ROOT"


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
    """Parse a price row into structured book data."""
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
    return {
        "product": product,
        "timestamp": ts,
        "bids": bids,
        "asks": asks,
        "mid": float(row.get("mid_price", 0)),
    }


def compute_mid(book):
    if book["bids"] and book["asks"]:
        return (book["bids"][0][0] + book["asks"][0][0]) / 2.0
    if book["bids"]:
        return float(book["bids"][0][0])
    if book["asks"]:
        return float(book["asks"][0][0])
    return book["mid"]


def compute_microprice(book):
    if not book["bids"] or not book["asks"]:
        return compute_mid(book)
    bb, bv = book["bids"][0]
    ba, av = book["asks"][0]
    total = bv + av
    if total <= 0:
        return (bb + ba) / 2.0
    return (bb * av + ba * bv) / total


def compute_imbalance(book):
    if not book["bids"] or not book["asks"]:
        return 0.0
    bv = book["bids"][0][1]
    av = book["asks"][0][1]
    total = bv + av
    if total <= 0:
        return 0.0
    return (bv - av) / total


def compute_spread(book):
    if not book["bids"] or not book["asks"]:
        return None
    return book["asks"][0][0] - book["bids"][0][0]


def compute_total_bid_vol(book):
    return sum(v for _, v in book["bids"])


def compute_total_ask_vol(book):
    return sum(v for _, v in book["asks"])


def compute_vol_imbalance(book):
    bv = compute_total_bid_vol(book)
    av = compute_total_ask_vol(book)
    total = bv + av
    if total <= 0:
        return 0.0
    return (bv - av) / total


def compute_mm10_mid(book):
    if not book["bids"] or not book["asks"]:
        return compute_mid(book)
    bid10 = None
    for p, v in book["bids"]:
        if v >= 10:
            bid10 = p
            break
    ask10 = None
    for p, v in book["asks"]:
        if v >= 10:
            ask10 = p
            break
    if bid10 is not None and ask10 is not None:
        return (bid10 + ask10) / 2.0
    return compute_mid(book)


print("=" * 80)
print("DEEP INDEPENDENT ANALYSIS FOR ROUND 1")
print("=" * 80)

# ============================================================================
# SECTION 1: ASH ANALYSIS - Finding improvement opportunities
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 1: ASH_COATED_OSMIUM DEEP ANALYSIS")
print("=" * 80)

all_ash_books = []
for day in DAYS:
    prices = load_prices(day)
    books = [parse_book(r) for r in prices if r["product"] == ASH]
    for b in books:
        b["day"] = day
    all_ash_books.extend(books)

# 1a: Ash imbalance -> future return analysis (more granular than research)
print("\n--- 1a: Ash Imbalance -> Future Return (granular buckets) ---")
ash_by_ts = defaultdict(list)
for b in all_ash_books:
    ash_by_ts[(b["day"], b["timestamp"])].append(b)

ash_series = []
for day in DAYS:
    day_books = sorted([b for b in all_ash_books if b["day"] == day], key=lambda x: x["timestamp"])
    for b in day_books:
        mid = compute_mid(b)
        imb = compute_imbalance(b)
        micro = compute_microprice(b)
        spread = compute_spread(b)
        vol_imb = compute_vol_imbalance(b)
        mm10 = compute_mm10_mid(b)
        ash_series.append({
            "day": day, "ts": b["timestamp"], "mid": mid,
            "imbalance": imb, "microprice": micro, "spread": spread,
            "vol_imbalance": vol_imb, "mm10_mid": mm10,
            "total_bid_vol": compute_total_bid_vol(b),
            "total_ask_vol": compute_total_ask_vol(b),
        })

# Compute future returns at various horizons
for i in range(len(ash_series)):
    for h in [1, 5, 10, 20, 50]:
        j = i + h
        if j < len(ash_series) and ash_series[j]["day"] == ash_series[i]["day"]:
            ash_series[i][f"ret_{h}"] = ash_series[j]["mid"] - ash_series[i]["mid"]

# Bucket imbalance into 10 buckets
imb_buckets = defaultdict(lambda: defaultdict(list))
for s in ash_series:
    imb = s["imbalance"]
    bucket = round(imb * 5) / 5  # 0.2-wide buckets
    bucket = max(-1.0, min(1.0, bucket))
    for h in [1, 5, 10, 20, 50]:
        key = f"ret_{h}"
        if key in s:
            imb_buckets[bucket][h].append(s[key])

print(f"{'Imbalance':>12} {'n':>6} {'ret_1':>8} {'ret_5':>8} {'ret_10':>8} {'ret_20':>8} {'ret_50':>8}")
for bucket in sorted(imb_buckets.keys()):
    n = len(imb_buckets[bucket].get(10, []))
    avgs = {}
    for h in [1, 5, 10, 20, 50]:
        vals = imb_buckets[bucket].get(h, [])
        avgs[h] = sum(vals) / len(vals) if vals else 0
    print(f"{bucket:>12.2f} {n:>6} {avgs[1]:>8.3f} {avgs[5]:>8.3f} {avgs[10]:>8.3f} {avgs[20]:>8.3f} {avgs[50]:>8.3f}")

# 1b: Ash spread analysis - is spread predictive?
print("\n--- 1b: Ash Spread -> Future Return ---")
spread_buckets = defaultdict(lambda: defaultdict(list))
for s in ash_series:
    sp = s["spread"]
    if sp is None:
        continue
    for h in [1, 5, 10, 20]:
        key = f"ret_{h}"
        if key in s:
            spread_buckets[sp][h].append(s[key])

print(f"{'Spread':>8} {'n':>6} {'ret_1':>8} {'ret_5':>8} {'ret_10':>8} {'ret_20':>8}")
for sp in sorted(spread_buckets.keys()):
    n = len(spread_buckets[sp].get(10, []))
    if n < 20:
        continue
    avgs = {}
    for h in [1, 5, 10, 20]:
        vals = spread_buckets[sp].get(h, [])
        avgs[h] = sum(vals) / len(vals) if vals else 0
    print(f"{sp:>8} {n:>6} {avgs[1]:>8.3f} {avgs[5]:>8.3f} {avgs[10]:>8.3f} {avgs[20]:>8.3f}")

# 1c: Ash volume imbalance (full book) vs top-of-book imbalance
print("\n--- 1c: Ash Volume Imbalance (full book) -> Future Return ---")
volimb_buckets = defaultdict(lambda: defaultdict(list))
for s in ash_series:
    vi = s["vol_imbalance"]
    bucket = round(vi * 5) / 5
    bucket = max(-1.0, min(1.0, bucket))
    for h in [1, 5, 10, 20]:
        key = f"ret_{h}"
        if key in s:
            volimb_buckets[bucket][h].append(s[key])

print(f"{'VolImbal':>10} {'n':>6} {'ret_1':>8} {'ret_5':>8} {'ret_10':>8} {'ret_20':>8}")
for bucket in sorted(volimb_buckets.keys()):
    n = len(volimb_buckets[bucket].get(10, []))
    if n < 10:
        continue
    avgs = {}
    for h in [1, 5, 10, 20]:
        vals = volimb_buckets[bucket].get(h, [])
        avgs[h] = sum(vals) / len(vals) if vals else 0
    print(f"{bucket:>10.2f} {n:>6} {avgs[1]:>8.3f} {avgs[5]:>8.3f} {avgs[10]:>8.3f} {avgs[20]:>8.3f}")

# 1d: Ash mid deviation from 10000 -> predictive of mean reversion?
print("\n--- 1d: Ash Mid Deviation from 10000 -> Future Return ---")
dev_buckets = defaultdict(lambda: defaultdict(list))
for s in ash_series:
    dev = s["mid"] - 10000.0
    bucket = round(dev / 2) * 2
    for h in [1, 5, 10, 20, 50]:
        key = f"ret_{h}"
        if key in s:
            dev_buckets[bucket][h].append(s[key])

print(f"{'MidDev':>8} {'n':>6} {'ret_1':>8} {'ret_5':>8} {'ret_10':>8} {'ret_20':>8} {'ret_50':>8}")
for bucket in sorted(dev_buckets.keys()):
    n = len(dev_buckets[bucket].get(10, []))
    if n < 10:
        continue
    avgs = {}
    for h in [1, 5, 10, 20, 50]:
        vals = dev_buckets[bucket].get(h, [])
        avgs[h] = sum(vals) / len(vals) if vals else 0
    print(f"{bucket:>8.0f} {n:>6} {avgs[1]:>8.3f} {avgs[5]:>8.3f} {avgs[10]:>8.3f} {avgs[20]:>8.3f} {avgs[50]:>8.3f}")

# 1e: Ash trade impact analysis
print("\n--- 1e: Ash Trade Impact Analysis ---")
for day in DAYS:
    trades = load_trades(day)
    ash_trades = [t for t in trades if t["symbol"] == ASH]
    day_books = sorted([s for s in ash_series if s["day"] == day], key=lambda x: x["ts"])
    ts_to_idx = {s["ts"]: i for i, s in enumerate(day_books)}

    buy_impacts = []
    sell_impacts = []
    for t in ash_trades:
        ts = int(t["timestamp"])
        price = float(t["price"])
        # Find nearest book state
        nearest = min(ts_to_idx.keys(), key=lambda x: abs(x - ts), default=None)
        if nearest is None:
            continue
        idx = ts_to_idx[nearest]
        if idx + 10 < len(day_books):
            mid_now = day_books[idx]["mid"]
            mid_future = day_books[idx + 10]["mid"]
            impact = mid_future - mid_now
            if price > mid_now:
                buy_impacts.append(impact)
            else:
                sell_impacts.append(impact)

    if buy_impacts:
        print(f"Day {day}: Buy-lift impact (h=10): {sum(buy_impacts)/len(buy_impacts):.3f} (n={len(buy_impacts)})")
    if sell_impacts:
        print(f"Day {day}: Sell-hit impact (h=10): {sum(sell_impacts)/len(sell_impacts):.3f} (n={len(sell_impacts)})")

# 1f: Ash autocorrelation of mid changes at different lags
print("\n--- 1f: Ash Mid-Change Autocorrelation ---")
for day in DAYS:
    day_books = sorted([s for s in ash_series if s["day"] == day], key=lambda x: x["ts"])
    changes = [day_books[i+1]["mid"] - day_books[i]["mid"] for i in range(len(day_books)-1)]
    n = len(changes)
    mean_c = sum(changes) / n if n > 0 else 0
    var_c = sum((c - mean_c)**2 for c in changes) / n if n > 0 else 1

    print(f"Day {day}: n_changes={n}, mean_change={mean_c:.4f}, std={math.sqrt(var_c):.4f}")
    for lag in [1, 2, 3, 5, 10, 20]:
        if lag >= n:
            continue
        cov = sum((changes[i] - mean_c) * (changes[i+lag] - mean_c) for i in range(n - lag)) / (n - lag)
        ac = cov / var_c if var_c > 0 else 0
        print(f"  lag {lag}: autocorr = {ac:.4f}")


# ============================================================================
# SECTION 2: PEPPER TEMPLATE REFINEMENT
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 2: PEPPER TEMPLATE REFINEMENT")
print("=" * 80)

all_pepper_books = []
for day in DAYS:
    prices = load_prices(day)
    books = [parse_book(r) for r in prices if r["product"] == PEPPER]
    for b in books:
        b["day"] = day
    all_pepper_books.extend(books)

pepper_series = []
for day in DAYS:
    day_books = sorted([b for b in all_pepper_books if b["day"] == day], key=lambda x: x["timestamp"])
    open_mid = None
    for b in day_books:
        mid = compute_mid(b)
        if open_mid is None:
            open_mid = mid
        offset = mid - open_mid
        progress = b["timestamp"] / 999900.0
        pepper_series.append({
            "day": day, "ts": b["timestamp"], "mid": mid,
            "open_mid": open_mid, "offset": offset,
            "progress": progress,
            "imbalance": compute_imbalance(b),
            "microprice": compute_microprice(b),
            "spread": compute_spread(b),
        })

# 2a: Extract finer template with 50 points
print("\n--- 2a: Finer Pepper Template (50 evenly-spaced points) ---")
N_POINTS = 50
template_offsets = []
for i in range(N_POINTS + 1):
    target_progress = i / N_POINTS
    day_values = []
    for day in DAYS:
        day_data = sorted([s for s in pepper_series if s["day"] == day], key=lambda x: x["ts"])
        # Find the two surrounding points
        closest = min(day_data, key=lambda x: abs(x["progress"] - target_progress))
        day_values.append(closest["offset"])
    avg_offset = sum(day_values) / len(day_values)
    template_offsets.append(round(avg_offset, 1))

print(f"PEPPER_TEMPLATE_OFFSETS_50 = [")
for i in range(0, len(template_offsets), 10):
    chunk = template_offsets[i:i+10]
    print(f"    {', '.join(f'{v}' for v in chunk)},")
print(f"]")

# 2b: Also compute template at 100 points for even finer resolution
print("\n--- 2b: Finer Pepper Template (100 evenly-spaced points) ---")
N_POINTS_100 = 100
template_offsets_100 = []
for i in range(N_POINTS_100 + 1):
    target_progress = i / N_POINTS_100
    day_values = []
    for day in DAYS:
        day_data = sorted([s for s in pepper_series if s["day"] == day], key=lambda x: x["ts"])
        closest = min(day_data, key=lambda x: abs(x["progress"] - target_progress))
        day_values.append(closest["offset"])
    avg_offset = sum(day_values) / len(day_values)
    template_offsets_100.append(round(avg_offset, 1))

print(f"PEPPER_TEMPLATE_OFFSETS_100 = [")
for i in range(0, len(template_offsets_100), 10):
    chunk = template_offsets_100[i:i+10]
    print(f"    {', '.join(f'{v}' for v in chunk)},")
print(f"]")

# 2c: Compute template residual statistics for v6's 31-point template
print("\n--- 2c: Template Residual Stats for v6 31-point vs 50-point vs 100-point ---")

V6_OFFSETS = [
    0.0, 35.8, 68.0, 103.2, 134.8, 168.3, 201.5, 234.8, 268.8, 301.5,
    334.8, 368.5, 399.8, 435.3, 467.5, 501.2, 533.8, 567.5, 602.0, 635.2,
    668.7, 701.0, 734.7, 768.0, 803.5, 834.7, 867.8, 900.8, 934.7, 967.8,
    1001.3,
]

def interp_offset(progress, offsets):
    progress = max(0.0, min(1.0, progress))
    scaled = progress * (len(offsets) - 1)
    lo = int(math.floor(scaled))
    hi = min(len(offsets) - 1, lo + 1)
    frac = scaled - lo
    return offsets[lo] + frac * (offsets[hi] - offsets[lo])

for name, offsets in [("v6_31pt", V6_OFFSETS), ("50pt", template_offsets), ("100pt", template_offsets_100)]:
    residuals = []
    for s in pepper_series:
        template_val = interp_offset(s["progress"], offsets)
        residual = s["offset"] - template_val
        residuals.append(residual)

    mean_r = sum(residuals) / len(residuals)
    std_r = math.sqrt(sum((r - mean_r)**2 for r in residuals) / len(residuals))
    mae = sum(abs(r) for r in residuals) / len(residuals)
    max_r = max(abs(r) for r in residuals)

    print(f"{name:>12}: mean={mean_r:.3f}, std={std_r:.3f}, MAE={mae:.3f}, max_abs={max_r:.3f}")


# 2d: Pepper imbalance conditional on residual state
print("\n--- 2d: Pepper Residual -> Future Return (conditional on imbalance) ---")
for imb_range_name, imb_lo, imb_hi in [("neg_hi", -1.0, -0.3), ("neg", -0.3, -0.1), ("flat", -0.1, 0.1), ("pos", 0.1, 0.3), ("pos_hi", 0.3, 1.0)]:
    bucket_rets = defaultdict(list)
    for s in pepper_series:
        if not (imb_lo <= s["imbalance"] < imb_hi):
            continue
        # Find template residual
        template_val = interp_offset(s["progress"], V6_OFFSETS)
        residual = s["offset"] - template_val
        # Bucket residual
        rbucket = round(residual / 2) * 2
        # Find future return
        idx = pepper_series.index(s)
        if idx + 10 < len(pepper_series) and pepper_series[idx + 10]["day"] == s["day"]:
            ret10 = pepper_series[idx + 10]["mid"] - s["mid"]
            bucket_rets[rbucket].append(ret10)

    print(f"\n  Imbalance range: {imb_range_name} ({imb_lo:.1f} to {imb_hi:.1f})")
    print(f"  {'Residual':>10} {'n':>6} {'ret_10':>8}")
    for rb in sorted(bucket_rets.keys()):
        vals = bucket_rets[rb]
        if len(vals) < 5:
            continue
        avg = sum(vals) / len(vals)
        print(f"  {rb:>10.0f} {len(vals):>6} {avg:>8.3f}")


# ============================================================================
# SECTION 3: ASH EXECUTION OPTIMIZATION ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 3: ASH EXECUTION OPTIMIZATION")
print("=" * 80)

# 3a: How often does Ash have mispriced levels we could take?
print("\n--- 3a: Ash Take Opportunity Analysis ---")
for day in DAYS:
    day_data = sorted([s for s in ash_series if s["day"] == day], key=lambda x: x["ts"])
    day_books = sorted([b for b in all_ash_books if b["day"] == day], key=lambda x: x["timestamp"])

    take_opps = {"buy": 0, "sell": 0, "total": 0}
    total_steps = 0
    for i, (s, b) in enumerate(zip(day_data, day_books)):
        total_steps += 1
        fair = 10000.0 + 0.65 * max(-3, min(3, s["mm10_mid"] - 10000.0))

        # Check if best ask is below fair - edge
        for edge in [2.0, 2.5, 3.0, 3.5]:
            if b["asks"] and b["asks"][0][0] < fair - edge:
                take_opps["buy"] += 1
                break
        for edge in [2.0, 2.5, 3.0, 3.5]:
            if b["bids"] and b["bids"][0][0] > fair + edge:
                take_opps["sell"] += 1
                break
        take_opps["total"] += 1

    print(f"Day {day}: buy_opps={take_opps['buy']}, sell_opps={take_opps['sell']}, total={take_opps['total']}")
    print(f"  Buy rate: {take_opps['buy']/total_steps*100:.1f}%, Sell rate: {take_opps['sell']/total_steps*100:.1f}%")

# 3b: Ash edge analysis - what's the optimal take edge?
print("\n--- 3b: Ash Optimal Take Edge (expected PnL per take) ---")
for take_edge in [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]:
    buy_pnls = []
    sell_pnls = []
    for day in DAYS:
        day_data = sorted([s for s in ash_series if s["day"] == day], key=lambda x: x["ts"])
        day_books = sorted([b for b in all_ash_books if b["day"] == day], key=lambda x: x["timestamp"])

        for i, (s, b) in enumerate(zip(day_data, day_books)):
            fair = 10000.0 + 0.65 * max(-3, min(3, s["mm10_mid"] - 10000.0))

            if b["asks"] and b["asks"][0][0] <= fair - take_edge:
                ask_price = b["asks"][0][0]
                # Expected PnL = fair - ask_price (immediate) or future mid - ask_price
                if i + 20 < len(day_data):
                    pnl = day_data[i + 20]["mid"] - ask_price
                    buy_pnls.append(pnl)

            if b["bids"] and b["bids"][0][0] >= fair + take_edge:
                bid_price = b["bids"][0][0]
                if i + 20 < len(day_data):
                    pnl = bid_price - day_data[i + 20]["mid"]
                    sell_pnls.append(pnl)

    total = buy_pnls + sell_pnls
    if total:
        avg_pnl = sum(total) / len(total)
        win_rate = sum(1 for p in total if p > 0) / len(total) * 100
        print(f"Edge {take_edge:.1f}: n={len(total):>5}, avg_pnl={avg_pnl:>7.3f}, win_rate={win_rate:.1f}%")

# 3c: Ash quote edge analysis - expected fill + PnL for passive quotes
print("\n--- 3c: Ash Passive Quote Analysis ---")
for quote_offset in [3.0, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0]:
    fills = 0
    total_pnl = 0
    total_quotes = 0
    for day in DAYS:
        day_data = sorted([s for s in ash_series if s["day"] == day], key=lambda x: x["ts"])
        day_books = sorted([b for b in all_ash_books if b["day"] == day], key=lambda x: x["timestamp"])

        for i, (s, b) in enumerate(zip(day_data, day_books)):
            fair = 10000.0
            bid_quote = math.floor(fair - quote_offset)
            ask_quote = math.ceil(fair + quote_offset)
            total_quotes += 1

            # Check if bid would fill (ask comes to or below our bid)
            if b["asks"] and b["asks"][0][0] <= bid_quote:
                fills += 1
                if i + 20 < len(day_data):
                    total_pnl += day_data[i + 20]["mid"] - bid_quote

            if b["bids"] and b["bids"][0][0] >= ask_quote:
                fills += 1
                if i + 20 < len(day_data):
                    total_pnl += ask_quote - day_data[i + 20]["mid"]

    fill_rate = fills / (total_quotes * 2) * 100 if total_quotes > 0 else 0
    avg_pnl = total_pnl / fills if fills > 0 else 0
    print(f"Offset {quote_offset:.1f}: fills={fills:>6}, fill_rate={fill_rate:.2f}%, avg_pnl={avg_pnl:.3f}")


# ============================================================================
# SECTION 4: CROSS-PRODUCT ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 4: CROSS-PRODUCT ANALYSIS")
print("=" * 80)

# 4a: Does Ash movement predict Pepper movement or vice versa?
print("\n--- 4a: Cross-Product Lead-Lag ---")
for day in DAYS:
    ash_day = sorted([s for s in ash_series if s["day"] == day], key=lambda x: x["ts"])
    pep_day = sorted([s for s in pepper_series if s["day"] == day], key=lambda x: x["ts"])

    # Build aligned series
    ash_ts_map = {s["ts"]: s for s in ash_day}
    pep_ts_map = {s["ts"]: s for s in pep_day}
    common_ts = sorted(set(ash_ts_map.keys()) & set(pep_ts_map.keys()))

    if len(common_ts) < 100:
        continue

    ash_changes = []
    pep_changes = []
    for i in range(1, len(common_ts)):
        t0 = common_ts[i-1]
        t1 = common_ts[i]
        ash_changes.append(ash_ts_map[t1]["mid"] - ash_ts_map[t0]["mid"])
        pep_changes.append(pep_ts_map[t1]["mid"] - pep_ts_map[t0]["mid"])

    n = len(ash_changes)
    # Cross-correlation at lag 0
    mean_a = sum(ash_changes) / n
    mean_p = sum(pep_changes) / n
    var_a = sum((a - mean_a)**2 for a in ash_changes) / n
    var_p = sum((p - mean_p)**2 for p in pep_changes) / n

    for lag in [0, 1, 2, -1, -2]:
        if lag >= 0:
            pairs = [(ash_changes[i], pep_changes[i+lag]) for i in range(n - abs(lag))]
        else:
            pairs = [(ash_changes[i-lag], pep_changes[i]) for i in range(n - abs(lag))]

        cov = sum((a - mean_a) * (p - mean_p) for a, p in pairs) / len(pairs)
        corr = cov / math.sqrt(var_a * var_p) if var_a > 0 and var_p > 0 else 0
        print(f"Day {day}: Ash change -> Pepper change at lag {lag:>2}: corr = {corr:.4f}")


# ============================================================================
# SECTION 5: PEPPER LATE SESSION BEHAVIOR
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 5: PEPPER LATE SESSION ANALYSIS")
print("=" * 80)

# 5a: Does Pepper ramp speed change through the session?
print("\n--- 5a: Pepper Ramp Speed by Session Phase ---")
for day in DAYS:
    day_data = sorted([s for s in pepper_series if s["day"] == day], key=lambda x: x["ts"])
    n = len(day_data)

    phases = [
        ("early", 0, n // 5),
        ("mid_early", n // 5, 2 * n // 5),
        ("mid", 2 * n // 5, 3 * n // 5),
        ("mid_late", 3 * n // 5, 4 * n // 5),
        ("late", 4 * n // 5, n),
    ]

    print(f"\nDay {day}:")
    for name, start, end in phases:
        if end <= start + 1:
            continue
        total_move = day_data[end-1]["mid"] - day_data[start]["mid"]
        total_time = day_data[end-1]["ts"] - day_data[start]["ts"]
        rate = total_move / (total_time / 100.0) if total_time > 0 else 0
        print(f"  {name:>12}: move={total_move:>7.1f}, rate/100ts={rate:.4f}")

# 5b: Pepper residual behavior in final 10% of session
print("\n--- 5b: Pepper End-of-Session Residual ---")
for day in DAYS:
    day_data = sorted([s for s in pepper_series if s["day"] == day], key=lambda x: x["ts"])
    n = len(day_data)

    late_data = day_data[int(0.9 * n):]
    residuals_late = []
    for s in late_data:
        template_val = interp_offset(s["progress"], V6_OFFSETS)
        residual = s["offset"] - template_val
        residuals_late.append(residual)

    if residuals_late:
        mean_r = sum(residuals_late) / len(residuals_late)
        std_r = math.sqrt(sum((r - mean_r)**2 for r in residuals_late) / len(residuals_late))
        print(f"Day {day}: late residual mean={mean_r:.3f}, std={std_r:.3f}")
        print(f"  Final mid: {late_data[-1]['mid']:.1f}, open_mid: {late_data[-1]['open_mid']:.1f}")
        print(f"  Total session move: {late_data[-1]['mid'] - day_data[0]['mid']:.1f}")


# ============================================================================
# SECTION 6: MARKET TRADE ANALYSIS FOR ASH
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 6: ASH MARKET TRADE FLOW ANALYSIS")
print("=" * 80)

print("\n--- 6a: Ash Trade Flow -> Future Return ---")
for day in DAYS:
    trades = load_trades(day)
    ash_trades = [t for t in trades if t["symbol"] == ASH]
    day_data = sorted([s for s in ash_series if s["day"] == day], key=lambda x: x["ts"])

    # Build cumulative flow score per timestamp
    trade_flow = defaultdict(int)
    for t in ash_trades:
        ts = int(t["timestamp"])
        price = float(t["price"])
        qty = int(t["quantity"])
        # Classify: nearest book state
        nearest_idx = min(range(len(day_data)), key=lambda i: abs(day_data[i]["ts"] - ts))
        mid = day_data[nearest_idx]["mid"]
        if price > mid:
            trade_flow[ts] += qty
        else:
            trade_flow[ts] -= qty

    # EMA of trade flow
    flow_ema = 0
    flow_ema_series = []
    for s in day_data:
        ts = s["ts"]
        flow_ema = 0.86 * flow_ema + trade_flow.get(ts, 0)
        flow_ema_series.append(flow_ema)

    # Bucket flow_ema and check future returns
    pos_flow_rets = []
    neg_flow_rets = []
    zero_flow_rets = []
    for i, (s, fe) in enumerate(zip(day_data, flow_ema_series)):
        if i + 10 >= len(day_data):
            break
        ret10 = day_data[i + 10]["mid"] - s["mid"]
        if fe > 3.0:
            pos_flow_rets.append(ret10)
        elif fe < -3.0:
            neg_flow_rets.append(ret10)
        else:
            zero_flow_rets.append(ret10)

    print(f"Day {day}:")
    if pos_flow_rets:
        print(f"  pos flow (n={len(pos_flow_rets)}): avg_ret10 = {sum(pos_flow_rets)/len(pos_flow_rets):.3f}")
    if neg_flow_rets:
        print(f"  neg flow (n={len(neg_flow_rets)}): avg_ret10 = {sum(neg_flow_rets)/len(neg_flow_rets):.3f}")
    if zero_flow_rets:
        print(f"  zero flow (n={len(zero_flow_rets)}): avg_ret10 = {sum(zero_flow_rets)/len(zero_flow_rets):.3f}")


# ============================================================================
# SECTION 7: SUMMARY OF FINDINGS AND STRATEGY HYPOTHESES
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 7: SUMMARY AND STRATEGY HYPOTHESES")
print("=" * 80)

print("""
Key findings to implement:
1. ASH imbalance signal is strong and not fully exploited in v6
2. ASH take edge of 3.5 may be too conservative - edge 2.5-3.0 could capture more
3. ASH market trade flow has predictive power similar to Pepper
4. Finer Pepper template (50+ points) reduces residual MAE further
5. Pepper ramp speed is very consistent across session phases
6. Cross-product correlation is weak - no lead-lag edge to exploit
""")
