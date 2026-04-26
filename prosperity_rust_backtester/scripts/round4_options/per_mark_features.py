"""Per-Mark feature store for the Round 4 dossier project.

For each (Mark, product) pair we materialise one CSV at
`prosperity-research/03_eda/round4/per_mark/<MARK>_<PRODUCT>.csv` with
one row per trade where this Mark participated. Each row carries the
microstructure context BEFORE and AFTER the trade so that downstream
phases (trigger classifier, side-rule, inventory dynamics, microstructure
footprint) can run as pure pandas-free pivots.

Columns
-------
- `ts`                   timestamp at which the trade was matched.
- `day`                  1, 2, 3.
- `side`                 'buy' if Mark bought at this print, 'sell' if Mark sold.
- `qty`, `price`         from the trade row.
- `counterparty`         name of the OTHER Mark on the print (or '_anon_').
- `mid_pre`              mid at last quote ≤ ts-100 (one tick before).
- `mid_post_5/20/100/500` mid at ts + 500/2000/10000/50000 ts units (= 5/20/
                         100/500 ticks). Falls back to nearest later quote.
- `spread_pre`           ask1 - bid1 from the pre-quote (mid_pre tick).
- `imb1/2/3_pre`         (bid_vol_k - ask_vol_k) / (bid_vol_k + ask_vol_k);
                         missing levels treated as 0/0 → 0.
- `depth_bid_pre`        sum bid_vol levels 1..3.
- `depth_ask_pre`        sum ask_vol levels 1..3.
- `microprice_pre`       (bid_vol_1 * ask_price_1 + ask_vol_1 * bid_price_1)
                         / (bid_vol_1 + ask_vol_1).
- `inventory_day`        running net position for this (Mark, product) RESET
                         each day at ts=0.
- `inventory_cum`        running net position for this (Mark, product) CARRIED
                         across days.
- `trades_since_last_5/20/100`   count of THIS Mark's prints in [ts-N*100, ts).
- `trades_other_mark_since_last_5/20/100`   count of OTHER Marks' prints in
                                            same window, same product.
- `recent_ret_5/20/100`  (mid_pre - mid_at(ts - N*100)) — raw price diff in
                         ticks (we keep the raw price diff so that vol/lambda
                         features stay on the same scale as Kyle's lambda).
- `realised_vol_100`     stdev of mid diffs over the trailing 100 ticks.
- `aggressor`            'buy' if trade price >= ask1_pre (someone lifted the
                         ask), 'sell' if price <= bid1_pre, else 'ambiguous'.
                         For a Mark-side classification: an `aggressor=='buy'`
                         row WITH `side=='buy'` means this Mark was the
                         aggressor; `side=='sell'` means this Mark was the
                         passive seller (their resting offer got hit).
- `adverse_select_5/20/100`   signed-by-trade-direction mid move at h=5/20/100:
                              for buys = mid_post - price; for sells = price
                              - mid_post. Positive = good for this Mark.

Outputs
-------
- One CSV per (Mark, product) pair under `per_mark/`.
- One index CSV `_index.csv` with row counts.

Usage
-----
    python3 per_mark_features.py [--horizon-ts 100]
"""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Optional, Tuple

TICK_TS = 100  # 1 tick = 100 ts units in Round 4 data.


def _as_int(s: str) -> Optional[int]:
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


def _as_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def load_quotes(prices_path: Path) -> Dict[str, Dict[int, dict]]:
    """Returns {product: {ts: quote_row}}."""
    out: Dict[str, Dict[int, dict]] = defaultdict(dict)
    with prices_path.open() as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            ts = _as_int(row.get("timestamp", ""))
            prod = row.get("product", "")
            if ts is None or not prod:
                continue
            out[prod][ts] = row
    return out


def quote_field(row: dict, key: str) -> Optional[float]:
    raw = row.get(key, "")
    if raw == "" or raw is None:
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None


def mid_at_or_after(quotes: Dict[int, dict], ts: int, max_step: int = 200) -> Optional[float]:
    """First quote at or after ts (within max_step ticks)."""
    for step in range(max_step):
        key = ts + step * TICK_TS
        if key in quotes:
            return quote_field(quotes[key], "mid_price")
    return None


def mid_at_or_before(quotes: Dict[int, dict], ts: int, max_step: int = 200) -> Optional[float]:
    """Most recent quote at or before ts."""
    for step in range(max_step):
        key = ts - step * TICK_TS
        if key in quotes and key >= 0:
            mid = quote_field(quotes[key], "mid_price")
            if mid is not None:
                return mid
    return None


def quote_at_or_before(quotes: Dict[int, dict], ts: int, max_step: int = 200) -> Optional[dict]:
    """Most recent full quote row at or before ts."""
    for step in range(max_step):
        key = ts - step * TICK_TS
        if key in quotes and key >= 0:
            return quotes[key]
    return None


def imb(bid_vol: Optional[float], ask_vol: Optional[float]) -> float:
    bv = bid_vol or 0.0
    av = ask_vol or 0.0
    den = bv + av
    if den == 0:
        return 0.0
    return (bv - av) / den


def microprice(quote: dict) -> Optional[float]:
    bv = quote_field(quote, "bid_volume_1")
    av = quote_field(quote, "ask_volume_1")
    bp = quote_field(quote, "bid_price_1")
    ap = quote_field(quote, "ask_price_1")
    if None in (bv, av, bp, ap) or (bv + av) == 0:
        return None
    return (bv * ap + av * bp) / (bv + av)


def realised_vol(quotes: Dict[int, dict], ts: int, lookback_ticks: int) -> Optional[float]:
    """Stdev of mid first differences over the last `lookback_ticks` ticks
    ending at ts (exclusive of ts)."""
    diffs = []
    prev = None
    for step in range(lookback_ticks, 0, -1):
        key = ts - step * TICK_TS
        if key in quotes:
            mid = quote_field(quotes[key], "mid_price")
            if mid is not None:
                if prev is not None:
                    diffs.append(mid - prev)
                prev = mid
    if len(diffs) < 4:
        return None
    return statistics.pstdev(diffs)


def aggressor(price: float, quote_pre: Optional[dict]) -> str:
    if quote_pre is None:
        return "ambiguous"
    bid1 = quote_field(quote_pre, "bid_price_1")
    ask1 = quote_field(quote_pre, "ask_price_1")
    if ask1 is not None and price >= ask1 - 1e-6:
        return "buy"
    if bid1 is not None and price <= bid1 + 1e-6:
        return "sell"
    return "ambiguous"


def per_mark_features(dataset_root: Path, out_dir: Path) -> Dict[str, int]:
    """Run the per-Mark feature build. Returns {file_stem: n_rows}."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) load all quotes per (day, product). We process one day at a time so
    #    the recency-window lookups don't need to span days.
    # 2) accumulate per-(mark, product) rows in memory; flush at the end.
    rows_by_pair: Dict[Tuple[str, str], List[dict]] = defaultdict(list)

    # Per (mark, product) cumulative inventory across days.
    inv_cum: Dict[Tuple[str, str], int] = defaultdict(int)

    for day in (1, 2, 3):
        prices = dataset_root / f"prices_round_4_day_{day}.csv"
        trades = dataset_root / f"trades_round_4_day_{day}.csv"
        if not (prices.exists() and trades.exists()):
            continue

        quotes_by_product = load_quotes(prices)

        # Per-day recency tracking: per (mark, product), keep a deque of
        # (timestamp, qty, side) for the trailing window. We bound it at the
        # 100-tick lookback (10000 ts units).
        recent_self: Dict[Tuple[str, str], deque] = defaultdict(lambda: deque(maxlen=200))
        recent_other: Dict[Tuple[str, str], deque] = defaultdict(lambda: deque(maxlen=400))
        # Per-day inventory.
        inv_day: Dict[Tuple[str, str], int] = defaultdict(int)

        with trades.open() as f:
            reader = csv.DictReader(f, delimiter=";")
            trades_rows = list(reader)

        for raw in trades_rows:
            ts = _as_int(raw.get("timestamp", ""))
            buyer = (raw.get("buyer", "") or "_anon_").strip()
            seller = (raw.get("seller", "") or "_anon_").strip()
            symbol = raw.get("symbol", "")
            price = _as_float(raw.get("price", ""))
            qty = _as_float(raw.get("quantity", ""))
            if ts is None or not symbol or price is None or qty is None:
                continue

            qprod = quotes_by_product.get(symbol)
            if not qprod:
                continue

            quote_pre = quote_at_or_before(qprod, ts - TICK_TS)
            mid_pre = quote_field(quote_pre, "mid_price") if quote_pre else None
            spread_pre = (
                (quote_field(quote_pre, "ask_price_1") or 0.0)
                - (quote_field(quote_pre, "bid_price_1") or 0.0)
                if quote_pre
                else None
            )
            i1 = imb(
                quote_field(quote_pre, "bid_volume_1") if quote_pre else None,
                quote_field(quote_pre, "ask_volume_1") if quote_pre else None,
            )
            i2 = imb(
                (quote_field(quote_pre, "bid_volume_1") or 0.0)
                + (quote_field(quote_pre, "bid_volume_2") or 0.0)
                if quote_pre else None,
                (quote_field(quote_pre, "ask_volume_1") or 0.0)
                + (quote_field(quote_pre, "ask_volume_2") or 0.0)
                if quote_pre else None,
            )
            i3 = imb(
                (quote_field(quote_pre, "bid_volume_1") or 0.0)
                + (quote_field(quote_pre, "bid_volume_2") or 0.0)
                + (quote_field(quote_pre, "bid_volume_3") or 0.0)
                if quote_pre else None,
                (quote_field(quote_pre, "ask_volume_1") or 0.0)
                + (quote_field(quote_pre, "ask_volume_2") or 0.0)
                + (quote_field(quote_pre, "ask_volume_3") or 0.0)
                if quote_pre else None,
            )
            depth_bid = (
                (quote_field(quote_pre, "bid_volume_1") or 0.0)
                + (quote_field(quote_pre, "bid_volume_2") or 0.0)
                + (quote_field(quote_pre, "bid_volume_3") or 0.0)
                if quote_pre else None
            )
            depth_ask = (
                (quote_field(quote_pre, "ask_volume_1") or 0.0)
                + (quote_field(quote_pre, "ask_volume_2") or 0.0)
                + (quote_field(quote_pre, "ask_volume_3") or 0.0)
                if quote_pre else None
            )
            mp_pre = microprice(quote_pre) if quote_pre else None

            agg = aggressor(price, quote_pre)

            mid_post_5 = mid_at_or_after(qprod, ts + 5 * TICK_TS)
            mid_post_20 = mid_at_or_after(qprod, ts + 20 * TICK_TS)
            mid_post_100 = mid_at_or_after(qprod, ts + 100 * TICK_TS)
            mid_post_500 = mid_at_or_after(qprod, ts + 500 * TICK_TS)

            # recent_ret_N: mid_pre minus mid at ts - N*100
            def _recent_ret(N: int) -> Optional[float]:
                back = mid_at_or_before(qprod, ts - N * TICK_TS)
                if back is None or mid_pre is None:
                    return None
                return mid_pre - back

            r5 = _recent_ret(5)
            r20 = _recent_ret(20)
            r100 = _recent_ret(100)

            rv100 = realised_vol(qprod, ts, 100)

            # For each side participant ('buy' / 'sell'), emit a row indexed
            # under that Mark.
            for mark, side, partner in (
                (buyer, "buy", seller),
                (seller, "sell", buyer),
            ):
                if mark == "_anon_":
                    continue
                key = (mark, symbol)

                # --- recency counters ---
                self_dq = recent_self[key]
                window_lo = ts - 100 * TICK_TS  # 100-tick lookback
                # purge stale entries
                while self_dq and self_dq[0] < window_lo:
                    self_dq.popleft()
                t5 = sum(1 for x in self_dq if x >= ts - 5 * TICK_TS)
                t20 = sum(1 for x in self_dq if x >= ts - 20 * TICK_TS)
                t100 = len(self_dq)

                other_dq = recent_other[key]
                while other_dq and other_dq[0] < window_lo:
                    other_dq.popleft()
                ot5 = sum(1 for x in other_dq if x >= ts - 5 * TICK_TS)
                ot20 = sum(1 for x in other_dq if x >= ts - 20 * TICK_TS)
                ot100 = len(other_dq)

                # --- inventory: this trade affects inventory for this Mark ---
                signed_qty = int(qty) if side == "buy" else -int(qty)
                inv_day_after = inv_day[key] + signed_qty
                inv_cum_after = inv_cum[key] + signed_qty

                # --- adverse selection (signed by THIS Mark's trade direction) ---
                def _adv(post: Optional[float]) -> Optional[float]:
                    if post is None:
                        return None
                    return (post - price) if side == "buy" else (price - post)

                adv5 = _adv(mid_post_5)
                adv20 = _adv(mid_post_20)
                adv100 = _adv(mid_post_100)

                rows_by_pair[key].append({
                    "ts": ts,
                    "day": day,
                    "side": side,
                    "qty": int(qty),
                    "price": price,
                    "counterparty": partner,
                    "mid_pre": mid_pre,
                    "mid_post_5": mid_post_5,
                    "mid_post_20": mid_post_20,
                    "mid_post_100": mid_post_100,
                    "mid_post_500": mid_post_500,
                    "spread_pre": spread_pre,
                    "imb1_pre": round(i1, 4),
                    "imb2_pre": round(i2, 4),
                    "imb3_pre": round(i3, 4),
                    "depth_bid_pre": depth_bid,
                    "depth_ask_pre": depth_ask,
                    "microprice_pre": mp_pre,
                    "inventory_day_pre": inv_day[key],
                    "inventory_day": inv_day_after,
                    "inventory_cum_pre": inv_cum[key],
                    "inventory_cum": inv_cum_after,
                    "trades_since_last_5": t5,
                    "trades_since_last_20": t20,
                    "trades_since_last_100": t100,
                    "trades_other_mark_since_last_5": ot5,
                    "trades_other_mark_since_last_20": ot20,
                    "trades_other_mark_since_last_100": ot100,
                    "recent_ret_5": r5,
                    "recent_ret_20": r20,
                    "recent_ret_100": r100,
                    "realised_vol_100": rv100,
                    "aggressor": agg,
                    "adverse_select_5": adv5,
                    "adverse_select_20": adv20,
                    "adverse_select_100": adv100,
                })

                # update post-state
                inv_day[key] = inv_day_after
                inv_cum[key] = inv_cum_after
                self_dq.append(ts)
                # add this trade to OTHER Marks' "other-mark recent" deque too
                # (so e.g. Mark 14 sees Mark 38's prints in their recent_other)
            # add every Mark-vs-other accounting:
            #   for each Mark active in the market on this product, record this
            #   trade as "other-mark" for everyone except the principals. We
            #   approximate with: each (Mark, symbol) deque receives the trade
            #   when Mark is NOT the buyer or seller. Implemented during dossier
            #   phase via the per-Mark CSV; here we only need recent_other for
            #   the two principals' VIEW of the OTHER side. Already added below.
            for mark in (buyer, seller):
                if mark == "_anon_":
                    continue
                # this Mark's "other_mark recent" deque should NOT include their
                # own trades (handled above) but SHOULD include the partner's
                # trade. The partner's perspective is symmetric: from their
                # angle, this trade IS their own. So we add the trade to
                # `recent_other[(other_mark_for_each_other_mark, symbol)]`...
                pass

            # For "other Mark" tracking, append to each principal's other_dq the
            # trade time IF the principal was not the participant. Since both
            # principals already ARE participants in this trade, the trade
            # itself is not an "other-mark" event for them. Their own deque was
            # updated above. Other Marks (not on this trade) would need to know
            # about it — we approximate by using a global per-product trade
            # stream and re-deriving "other-mark" counts at row-emit time. The
            # naive deque pattern above already captures self-counts; for
            # other-mark counts we use a per-product deque keyed by symbol.

        # Re-derive other-mark counters with a per-product trade timeline.
        # (This is cheaper to do in a second pass than to maintain
        # cross-cutting deques inline.)
        timeline_by_product: Dict[str, List[Tuple[int, str, str]]] = defaultdict(list)
        for raw in trades_rows:
            ts = _as_int(raw.get("timestamp", ""))
            buyer = (raw.get("buyer", "") or "_anon_").strip()
            seller = (raw.get("seller", "") or "_anon_").strip()
            symbol = raw.get("symbol", "")
            if ts is None or not symbol:
                continue
            timeline_by_product[symbol].append((ts, buyer, seller))

        # For every emitted row from THIS day, re-compute other-mark counters
        # from the timeline. Identify rows by (mark, product, ts, side).
        # Build an index: per (mark, product), list of timeline events where
        # mark is NOT a participant.
        for (mark, product), rows in rows_by_pair.items():
            tl = timeline_by_product.get(product, [])
            other_events = [t for (t, b, s) in tl if mark not in (b, s)]
            other_events.sort()
            for r in rows:
                if r["day"] != day:
                    continue
                ts = r["ts"]
                # binary search for events in (ts - 100*TICK_TS, ts)
                lo5 = ts - 5 * TICK_TS
                lo20 = ts - 20 * TICK_TS
                lo100 = ts - 100 * TICK_TS
                # linear is fine — at most 100 trades/day per product
                c5 = c20 = c100 = 0
                for et in other_events:
                    if et >= ts:
                        break
                    if et > lo100:
                        c100 += 1
                    if et > lo20:
                        c20 += 1
                    if et > lo5:
                        c5 += 1
                r["trades_other_mark_since_last_5"] = c5
                r["trades_other_mark_since_last_20"] = c20
                r["trades_other_mark_since_last_100"] = c100

    # Write per-(mark, product) CSVs and an index.
    counts: Dict[str, int] = {}
    columns = [
        "ts", "day", "side", "qty", "price", "counterparty",
        "mid_pre", "mid_post_5", "mid_post_20", "mid_post_100", "mid_post_500",
        "spread_pre",
        "imb1_pre", "imb2_pre", "imb3_pre",
        "depth_bid_pre", "depth_ask_pre", "microprice_pre",
        "inventory_day_pre", "inventory_day",
        "inventory_cum_pre", "inventory_cum",
        "trades_since_last_5", "trades_since_last_20", "trades_since_last_100",
        "trades_other_mark_since_last_5", "trades_other_mark_since_last_20",
        "trades_other_mark_since_last_100",
        "recent_ret_5", "recent_ret_20", "recent_ret_100",
        "realised_vol_100",
        "aggressor",
        "adverse_select_5", "adverse_select_20", "adverse_select_100",
    ]

    for (mark, product), rows in sorted(rows_by_pair.items()):
        safe_mark = mark.replace(" ", "_")
        path = out_dir / f"{safe_mark}_{product}.csv"
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=columns, delimiter=";")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        counts[path.name] = len(rows)

    idx_path = out_dir / "_index.csv"
    with idx_path.open("w", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["file", "n_rows"])
        for k, v in sorted(counts.items()):
            w.writerow([k, v])

    return counts


def main() -> int:
    here = Path(__file__).resolve().parent
    default_data = here.parents[1] / "datasets" / "round4"
    default_out = (
        here.parents[2] / "prosperity-research" / "03_eda" / "round4" / "per_mark"
    )
    p = argparse.ArgumentParser()
    p.add_argument("--dataset-root", type=Path, default=default_data)
    p.add_argument("--out-dir", type=Path, default=default_out)
    args = p.parse_args()

    counts = per_mark_features(args.dataset_root, args.out_dir)
    total = sum(counts.values())
    print(f"wrote {len(counts)} per-(Mark, product) files, total {total} rows -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
