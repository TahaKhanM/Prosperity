"""Prosperity 4 Round 3 — IMC matching-engine probe trader v1.

Purpose
=======
Reverse-engineer the OFFICIAL IMC backtester's order-matching rules by
running a battery of carefully-scheduled, deterministic experiments at
known tick offsets and emitting tagged diagnostic lines to stdout.

Each experiment (E##) tests a single hypothesis. Because our local Python
and Rust backtesters bake different assumptions into their matching loops,
any source-to-source divergence in fills under this trader isolates a
specific engine rule.

Output contract
---------------
The trader prints exactly one line per probe event to stdout in the form:

    PROBE eid=E05 ts=2000 product=HYDROGEL_PACK action=BUY price=10023 qty=26 \
        book=b1=10011x8,b2=10003x13|a1=10019x12,a2=10022x13,a3=10023x1 \
        pos_before=0 limit=200 note=waterfall_sum3

These lines appear in the IMC submission's `logs[*].lambdaLog` field and in
local BT stdout. A companion diff tool joins them to fills from the
`tradeHistory` section to produce a 3-way comparison.

Safety
------
- Every probe self-flattens by its declared end-tick so subsequent probes
  run against a clean position.
- Destructive / position-heavy probes use VEV_6500 (cheap, low vega) rather
  than HYDROGEL_PACK where possible.
- All probes use integer prices and integer quantities. No `None` orders.
- Position-limit probes are explicitly designed to trigger rejection, but
  they respect the documented aggregation rule so nothing is "accidentally"
  filled past a hard limit.

Implementation notes
--------------------
- traderData carries a compact JSON state machine so we can recover across
  ticks if the runtime re-instantiates the class.
- The trader is pure: no globals, no file I/O, no randomness. Repeatable.
- Returns (orders, conversions, traderData) every tick — submission safe.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState, Trade


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

H = "HYDROGEL_PACK"          # limit 200
VE = "VELVETFRUIT_EXTRACT"   # limit 200
VEV65 = "VEV_6500"           # limit 300 — cheap deep-OTM
VEV60 = "VEV_6000"           # limit 300 — cheap deep-OTM

POS_LIMITS = {
    H: 200,
    VE: 200,
    VEV65: 300,
    VEV60: 300,
}

SCHEMA_VERSION = 1


# ---------------------------------------------------------------------------
# Probe schedule.
#
# Each entry describes when a probe fires and what it does. Probe IDs are
# stable strings so the diff tool can join across backtesters.
#
# "fire" semantics:
#   single_ts  → run exactly on this tick
#   range      → run every tick in [start, end] inclusive (for resting probes)
# ---------------------------------------------------------------------------

PROBES: List[Dict] = [
    # E00: long baseline — no orders whatsoever.
    {"eid": "E00_IDLE_A",  "mode": "range",     "start": 0,    "end": 999},

    # E01: one-shot cross the best ask on HYDROGEL with tiny size. Most
    # basic sanity check — confirms "order @ best_ask fills @ best_ask".
    {"eid": "E01_CROSS_ASK_TOP",   "mode": "single_ts", "ts": 1000, "product": H, "side": "BUY", "mode2": "cross_top_ask",  "qty": 1},

    # E02: one-shot cross the best bid on HYDROGEL with tiny size.
    {"eid": "E02_CROSS_BID_TOP",   "mode": "single_ts", "ts": 1100, "product": H, "side": "SELL", "mode2": "cross_top_bid", "qty": 1},

    # E03: flatten HYDROGEL back to 0 at market.
    {"eid": "E03_FLATTEN_H",       "mode": "single_ts", "ts": 1200, "product": H, "side": "AUTO_FLAT"},

    # E04: cross top ask on VE with qty 1.
    {"eid": "E04_CROSS_ASK_TOP_VE","mode": "single_ts", "ts": 1400, "product": VE, "side": "BUY", "mode2": "cross_top_ask", "qty": 1},

    # E05: flatten VE.
    {"eid": "E05_FLATTEN_VE",      "mode": "single_ts", "ts": 1500, "product": VE, "side": "AUTO_FLAT"},

    # E06: WATERFALL — BUY sum(levels 1..3 ask volumes) at level-3 ask price.
    # Expected official behavior: fully fills at each level's price.
    {"eid": "E06_WATERFALL_SUM3",  "mode": "single_ts", "ts": 2000, "product": H, "side": "BUY", "mode2": "waterfall_sum_asks", "cap_qty": 100},

    # E07: WATERFALL + excess above the book. Price far above level-3 ask.
    # Qty = sum_levels + 20. Does the excess 20 find phantom liquidity
    # (historical external trades) or is it silently dropped?
    {"eid": "E07_WATERFALL_EXCESS","mode": "single_ts", "ts": 2100, "product": H, "side": "BUY", "mode2": "waterfall_plus_excess", "excess_qty": 20, "cap_qty": 100},

    # E08: flatten HYDROGEL after waterfall tests.
    {"eid": "E08_FLATTEN_H",       "mode": "single_ts", "ts": 2200, "product": H, "side": "AUTO_FLAT"},

    # E09: RESTING BUY below best_bid — should NEVER cross the book. Only
    # fills if an external trade occurs at or below this price AND the
    # engine considers it liquidity for us. This is the key divergence
    # test. Resubmit every tick in the range so the order is always live.
    {"eid": "E09_RESTING_BELOW_BB","mode": "range", "start": 3000, "end": 3499, "product": VE, "side": "BUY", "mode2": "resting_below_best_bid", "offset": 1, "qty": 5},

    # E10: RESTING BUY at exactly best_bid (join the queue). This should
    # see some fills in both locals (they match at order.price <= trade.price
    # against historical external trades at same price).
    {"eid": "E10_RESTING_JOIN_BB", "mode": "range", "start": 3500, "end": 3999, "product": VE, "side": "BUY", "mode2": "resting_join_best_bid", "qty": 5},

    # E11: flatten VE.
    {"eid": "E11_FLATTEN_VE",      "mode": "single_ts", "ts": 4000, "product": VE, "side": "AUTO_FLAT"},

    # E12: POSITION LIMIT edge — qty = remaining_capacity + 1. Expected
    # full rejection of all orders on that product in that tick.
    {"eid": "E12_POSLIMIT_OVER1",  "mode": "single_ts", "ts": 4200, "product": VEV65, "side": "BUY", "mode2": "poslimit_over_by", "over_by": 1, "price_mode": "cross_top_ask"},

    # E13: POSITION LIMIT exact — qty = remaining_capacity. Expected full
    # fill (what the book supports).
    {"eid": "E13_POSLIMIT_EXACT",  "mode": "single_ts", "ts": 4300, "product": VEV65, "side": "BUY", "mode2": "poslimit_exact", "price_mode": "cross_top_ask"},

    # E14: POSITION LIMIT aggregation — two orders whose sum > capacity,
    # each individually valid. Documented rule: ALL rejected.
    {"eid": "E14_POSLIMIT_AGG",    "mode": "single_ts", "ts": 4400, "product": VEV65, "side": "BUY", "mode2": "poslimit_agg_over", "price_mode": "cross_top_ask"},

    # E15: flatten VEV65.
    {"eid": "E15_FLATTEN_V65",     "mode": "single_ts", "ts": 4500, "product": VEV65, "side": "AUTO_FLAT"},

    # E16: SELF-CROSS — simultaneous BUY at high price and SELL at low
    # price on the same product in the same tick. Does the engine match
    # these with each other (self-trade) or only against the external book?
    {"eid": "E16_SELFCROSS",       "mode": "single_ts", "ts": 5000, "product": VEV65, "side": "SELF_CROSS", "qty": 3},

    # E17: flatten.
    {"eid": "E17_FLATTEN_V65",     "mode": "single_ts", "ts": 5100, "product": VEV65, "side": "AUTO_FLAT"},

    # E18: QTY ZERO order. Malformed but schema-valid.
    {"eid": "E18_QTY_ZERO",        "mode": "single_ts", "ts": 5300, "product": VEV65, "side": "BUY", "mode2": "qty_zero"},

    # E19: DUPLICATE same-side same-price — two Orders for the same product,
    # side, price. Should aggregate for position-limit purposes and both
    # should fill (volume permitting).
    {"eid": "E19_DUPLICATE_BUY",   "mode": "single_ts", "ts": 5400, "product": VEV65, "side": "BUY", "mode2": "duplicate_orders", "qty": 2},

    # E20: flatten.
    {"eid": "E20_FLATTEN_V65",     "mode": "single_ts", "ts": 5500, "product": VEV65, "side": "AUTO_FLAT"},

    # E21: PRICE-BELOW-ZERO probe on VEV_6500. Try BUY at price 0 when best
    # ask is typically 1. Should not fill (no ask <= 0). Does the engine
    # accept price=0 at all?
    {"eid": "E21_PRICE_ZERO_BUY",  "mode": "single_ts", "ts": 6000, "product": VEV65, "side": "BUY", "mode2": "explicit_price", "price": 0, "qty": 1},

    # E22: SELL at explicit price 0 on VEV_6500. best_bid usually is 0, so
    # this is a "join the bid" order — should fill if external trades hit 0.
    {"eid": "E22_SELL_AT_ZERO",    "mode": "single_ts", "ts": 6100, "product": VEV65, "side": "SELL", "mode2": "explicit_price", "price": 0, "qty": 1},

    # E23: flatten.
    {"eid": "E23_FLATTEN_V65",     "mode": "single_ts", "ts": 6200, "product": VEV65, "side": "AUTO_FLAT"},

    # E24: LONG RESTING SELL on VELVETFRUIT 1 tick ABOVE best ask. Tests
    # whether external SELL-type trades (seller="") that happen at this
    # price count as fills for us in local vs official engines.
    {"eid": "E24_RESTING_ABOVE_BA","mode": "range", "start": 7000, "end": 7499, "product": VE, "side": "SELL", "mode2": "resting_above_best_ask", "offset": 1, "qty": 5},

    # E25: flatten VE.
    {"eid": "E25_FLATTEN_VE",      "mode": "single_ts", "ts": 7500, "product": VE, "side": "AUTO_FLAT"},

    # E26: wide RESTING on HYDROGEL far from mid. 1-tick exposure with a
    # BUY 15 below best_bid, SELL 15 above best_ask. Measures pure "fill
    # against external trade" noise.
    {"eid": "E26_WIDE_RESTING_H",  "mode": "range", "start": 8000, "end": 8499, "product": H, "side": "WIDE_QUOTE", "offset": 15, "qty": 3},

    # E27: flatten HYDROGEL (may be needed).
    {"eid": "E27_FLATTEN_H",       "mode": "single_ts", "ts": 8500, "product": H, "side": "AUTO_FLAT"},

    # E28: final idle, no orders at all.
    {"eid": "E28_IDLE_END",        "mode": "range", "start": 9000, "end": 9999},
]


# Pre-index single-timestamp probes and active range probes for O(1) lookup.
_SINGLE_PROBES_BY_TS: Dict[int, List[Dict]] = {}
_RANGE_PROBES: List[Dict] = []
for p in PROBES:
    if p["mode"] == "single_ts":
        _SINGLE_PROBES_BY_TS.setdefault(int(p["ts"]), []).append(p)
    else:
        _RANGE_PROBES.append(p)


# ---------------------------------------------------------------------------
# Helpers to describe book state compactly (for the PROBE log line).
# ---------------------------------------------------------------------------

def _fmt_levels(levels: List[Tuple[int, int]]) -> str:
    return ",".join(f"{p}x{abs(q)}" for p, q in levels)


def _depth_snapshot(od: Optional[OrderDepth]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """Return (sorted_bids_desc, sorted_asks_asc) as (price, positive_qty) tuples.

    Local backtesters (and the IMC datamodel) store sell_orders volumes as
    *negative* integers. We normalize to positive on the way out so all
    downstream math (waterfall sums, level volumes) is in one convention.
    """
    if od is None:
        return [], []
    bids = sorted(((int(p), int(abs(q))) for p, q in od.buy_orders.items()), key=lambda x: -x[0])
    asks = sorted(((int(p), int(abs(q))) for p, q in od.sell_orders.items()), key=lambda x: x[0])
    return bids, asks


def _compact_book(od: Optional[OrderDepth]) -> str:
    bids, asks = _depth_snapshot(od)
    b = _fmt_levels(bids[:3]) if bids else "EMPTY"
    a = _fmt_levels(asks[:3]) if asks else "EMPTY"
    return f"b={b}|a={a}"


def _best_bid_ask(od: Optional[OrderDepth]) -> Tuple[Optional[int], Optional[int]]:
    bids, asks = _depth_snapshot(od)
    bb = bids[0][0] if bids else None
    ba = asks[0][0] if asks else None
    return bb, ba


# ---------------------------------------------------------------------------
# Probe implementations — each returns List[Order] to submit this tick.
# They also print a single PROBE line describing intent.
# ---------------------------------------------------------------------------

def _log(eid: str, ts: int, product: str, action: str, price, qty, od: Optional[OrderDepth], pos_before: int, note: str = "") -> None:
    """Emit one PROBE diagnostic line to stdout."""
    limit = POS_LIMITS.get(product, -1)
    # price/qty can be int or list[tuple] — normalize for log.
    if isinstance(price, list):
        pq = ",".join(f"{p}x{q}" for p, q in price)
    else:
        pq = f"{price}x{qty}"
    print(
        f"PROBE eid={eid} ts={ts} product={product} action={action} "
        f"orders={pq} book={_compact_book(od)} pos_before={pos_before} "
        f"limit={limit} note={note}"
    )


def _emit_orders(product: str, items: List[Tuple[int, int]]) -> List[Order]:
    """items = [(price, signed_qty)]."""
    return [Order(product, int(price), int(qty)) for price, qty in items if qty != 0]


def _flatten_to_zero(product: str, od: Optional[OrderDepth], pos: int, eid: str, ts: int) -> List[Order]:
    """Aggressive flatten of current position at market. Safe fallback for
    products with empty books: emit nothing."""
    if pos == 0 or od is None:
        _log(eid, ts, product, "FLAT_NOOP", 0, 0, od, pos, note="already_flat_or_no_book")
        return []
    if pos > 0:
        # Need to SELL. Hit the bid.
        bb, _ = _best_bid_ask(od)
        if bb is None:
            _log(eid, ts, product, "FLAT_NO_BID", 0, 0, od, pos, note="no_bid_to_hit")
            return []
        orders = [(bb - 1, -pos)]  # sell below best_bid to waterfall down
        _log(eid, ts, product, "FLAT_SELL", bb - 1, -pos, od, pos, note=f"target_flat_{pos}")
        return _emit_orders(product, orders)
    else:
        # pos < 0, need to BUY. Lift the ask.
        _, ba = _best_bid_ask(od)
        if ba is None:
            _log(eid, ts, product, "FLAT_NO_ASK", 0, 0, od, pos, note="no_ask_to_lift")
            return []
        orders = [(ba + 1, -pos)]  # buy above best_ask
        _log(eid, ts, product, "FLAT_BUY", ba + 1, -pos, od, pos, note=f"target_flat_{pos}")
        return _emit_orders(product, orders)


def _run_single_probe(probe: Dict, state: TradingState) -> List[Order]:
    eid = probe["eid"]
    ts = state.timestamp
    product = probe.get("product")
    side = probe.get("side")
    mode2 = probe.get("mode2", "")
    od = state.order_depths.get(product) if product else None
    pos = state.position.get(product, 0) if product else 0

    if side == "AUTO_FLAT":
        return _flatten_to_zero(product, od, pos, eid, ts)

    if side == "BUY" and mode2 == "cross_top_ask":
        _, ba = _best_bid_ask(od)
        if ba is None:
            _log(eid, ts, product, "SKIP_NO_ASK", 0, 0, od, pos)
            return []
        qty = int(probe.get("qty", 1))
        _log(eid, ts, product, "BUY", ba, qty, od, pos, note="cross_top_ask")
        return _emit_orders(product, [(ba, qty)])

    if side == "SELL" and mode2 == "cross_top_bid":
        bb, _ = _best_bid_ask(od)
        if bb is None:
            _log(eid, ts, product, "SKIP_NO_BID", 0, 0, od, pos)
            return []
        qty = int(probe.get("qty", 1))
        _log(eid, ts, product, "SELL", bb, -qty, od, pos, note="cross_top_bid")
        return _emit_orders(product, [(bb, -qty)])

    if side == "BUY" and mode2 == "waterfall_sum_asks":
        bids, asks = _depth_snapshot(od)
        if not asks:
            _log(eid, ts, product, "SKIP_NO_ASK", 0, 0, od, pos)
            return []
        sum_vol = sum(q for _, q in asks[:3])
        cap = int(probe.get("cap_qty", 100))
        # Respect position limit.
        limit = POS_LIMITS.get(product, 100)
        max_room = limit - pos
        qty = min(sum_vol, cap, max_room)
        if qty <= 0:
            _log(eid, ts, product, "SKIP_NO_ROOM", 0, 0, od, pos, note=f"sum_vol={sum_vol}")
            return []
        price = asks[min(2, len(asks) - 1)][0]
        _log(eid, ts, product, "BUY", price, qty, od, pos, note=f"waterfall_sum3_vol={sum_vol}_cap={cap}")
        return _emit_orders(product, [(price, qty)])

    if side == "BUY" and mode2 == "waterfall_plus_excess":
        bids, asks = _depth_snapshot(od)
        if not asks:
            _log(eid, ts, product, "SKIP_NO_ASK", 0, 0, od, pos)
            return []
        sum_vol = sum(q for _, q in asks[:3])
        cap = int(probe.get("cap_qty", 100))
        excess = int(probe.get("excess_qty", 20))
        limit = POS_LIMITS.get(product, 100)
        max_room = limit - pos
        raw_qty = min(sum_vol + excess, cap + excess, max_room)
        if raw_qty <= 0:
            _log(eid, ts, product, "SKIP_NO_ROOM", 0, 0, od, pos)
            return []
        # Price way above the book to force "fill whatever is there".
        last_ask = asks[-1][0]
        price = last_ask + 50
        _log(eid, ts, product, "BUY", price, raw_qty, od, pos, note=f"waterfall_excess_sum_vol={sum_vol}_excess={excess}_cap={cap}")
        return _emit_orders(product, [(price, raw_qty)])

    if side == "BUY" and mode2 == "resting_below_best_bid":
        bb, _ = _best_bid_ask(od)
        if bb is None:
            return []
        offset = int(probe.get("offset", 1))
        qty = int(probe.get("qty", 5))
        price = bb - offset
        limit = POS_LIMITS.get(product, 100)
        if pos + qty > limit:
            return []
        # Only log every 100 ticks in a range probe to keep logs readable.
        if ts % 100 == 0:
            _log(eid, ts, product, "BUY_RESTING", price, qty, od, pos, note=f"offset_{offset}_below_bb")
        return _emit_orders(product, [(price, qty)])

    if side == "BUY" and mode2 == "resting_join_best_bid":
        bb, _ = _best_bid_ask(od)
        if bb is None:
            return []
        qty = int(probe.get("qty", 5))
        limit = POS_LIMITS.get(product, 100)
        if pos + qty > limit:
            return []
        if ts % 100 == 0:
            _log(eid, ts, product, "BUY_RESTING", bb, qty, od, pos, note="join_best_bid")
        return _emit_orders(product, [(bb, qty)])

    if side == "SELL" and mode2 == "resting_above_best_ask":
        _, ba = _best_bid_ask(od)
        if ba is None:
            return []
        offset = int(probe.get("offset", 1))
        qty = int(probe.get("qty", 5))
        price = ba + offset
        limit = POS_LIMITS.get(product, 100)
        if pos - qty < -limit:
            return []
        if ts % 100 == 0:
            _log(eid, ts, product, "SELL_RESTING", price, -qty, od, pos, note=f"offset_{offset}_above_ba")
        return _emit_orders(product, [(price, -qty)])

    if side == "WIDE_QUOTE":
        bb, ba = _best_bid_ask(od)
        if bb is None or ba is None:
            return []
        offset = int(probe.get("offset", 15))
        qty = int(probe.get("qty", 3))
        limit = POS_LIMITS.get(product, 100)
        buy_price = bb - offset
        sell_price = ba + offset
        orders = []
        if pos + qty <= limit:
            orders.append((buy_price, qty))
        if pos - qty >= -limit:
            orders.append((sell_price, -qty))
        if ts % 100 == 0:
            _log(eid, ts, product, "WIDE_QUOTE", orders, 0, od, pos, note=f"offset_{offset}")
        return _emit_orders(product, orders)

    if side == "BUY" and mode2 in ("poslimit_over_by", "poslimit_exact"):
        _, ba = _best_bid_ask(od)
        if ba is None:
            return []
        limit = POS_LIMITS.get(product, 100)
        room = limit - pos
        if mode2 == "poslimit_over_by":
            over_by = int(probe.get("over_by", 1))
            qty = room + over_by
            note = f"over_by_{over_by}_room_{room}"
        else:
            qty = room
            note = f"exact_room_{room}"
        if qty <= 0:
            _log(eid, ts, product, "SKIP_FULL", 0, 0, od, pos, note=f"already_at_limit_{limit}")
            return []
        _log(eid, ts, product, "BUY", ba, qty, od, pos, note=note)
        return _emit_orders(product, [(ba, qty)])

    if side == "BUY" and mode2 == "poslimit_agg_over":
        _, ba = _best_bid_ask(od)
        if ba is None:
            return []
        limit = POS_LIMITS.get(product, 100)
        room = limit - pos
        # Two orders each at room/2 + some overlap that pushes total past room.
        half = max(1, room // 2)
        q1 = half + 3
        q2 = half + 3  # sum = room + 6
        _log(eid, ts, product, "BUY_DUAL", [(ba, q1), (ba, q2)], 0, od, pos, note=f"sum={q1+q2}_room={room}")
        return _emit_orders(product, [(ba, q1), (ba, q2)])

    if side == "SELF_CROSS":
        bb, ba = _best_bid_ask(od)
        if bb is None or ba is None:
            return []
        qty = int(probe.get("qty", 3))
        # Buy well above mid; sell well below mid. Spread is typically tight.
        bp = ba + 5
        sp = bb - 5
        _log(eid, ts, product, "SELF_CROSS", [(bp, qty), (sp, -qty)], 0, od, pos, note="high_buy_low_sell")
        return _emit_orders(product, [(bp, qty), (sp, -qty)])

    if side == "BUY" and mode2 == "qty_zero":
        bb, ba = _best_bid_ask(od)
        if ba is None:
            return []
        _log(eid, ts, product, "BUY_ZERO_QTY", ba, 0, od, pos, note="schema_edge")
        return [Order(product, int(ba), 0)]

    if side == "BUY" and mode2 == "duplicate_orders":
        _, ba = _best_bid_ask(od)
        if ba is None:
            return []
        qty = int(probe.get("qty", 2))
        _log(eid, ts, product, "BUY_DUPLICATE", [(ba, qty), (ba, qty)], 0, od, pos, note="same_price_same_side")
        return _emit_orders(product, [(ba, qty), (ba, qty)])

    if mode2 == "explicit_price":
        price = int(probe["price"])
        qty = int(probe.get("qty", 1))
        signed = qty if side == "BUY" else -qty
        _log(eid, ts, product, side, price, signed, od, pos, note=f"explicit_price_{price}")
        return _emit_orders(product, [(price, signed)])

    # Unknown probe shape — log & skip.
    _log(eid, ts, product or "?", "UNKNOWN_MODE", 0, 0, od, pos, note=f"mode2={mode2}_side={side}")
    return []


# ---------------------------------------------------------------------------
# Trader
# ---------------------------------------------------------------------------


class Trader:
    def run(self, state: TradingState):
        ts = int(state.timestamp)
        orders: Dict[str, List[Order]] = {}

        # 1) Single-timestamp probes.
        for probe in _SINGLE_PROBES_BY_TS.get(ts, []):
            new_orders = _run_single_probe(probe, state)
            for o in new_orders:
                orders.setdefault(o.symbol, []).append(o)

        # 2) Range probes.
        for probe in _RANGE_PROBES:
            if probe["mode"] != "range":
                continue
            if ts < int(probe["start"]) or ts > int(probe["end"]):
                continue
            # IDLE probes just log once per range to mark the region.
            if probe.get("side") is None:
                if ts == int(probe["start"]) or ts == int(probe["end"]):
                    print(f"PROBE eid={probe['eid']} ts={ts} product=NONE action=IDLE_MARK")
                continue
            new_orders = _run_single_probe(probe, state)
            for o in new_orders:
                orders.setdefault(o.symbol, []).append(o)

        trader_data = json.dumps({"schema": SCHEMA_VERSION, "ts": ts})
        return orders, 0, trader_data