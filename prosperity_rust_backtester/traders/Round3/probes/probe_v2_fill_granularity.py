"""Prosperity 4 Round 3 — IMC matching-engine probe trader v2 (fill granularity).

Why a v2
========
v1 (`probe_v1_matching.py`) settled the basics: top-of-book crosses, position-
limit aggregation, qty=0 / price=0 schema edges, self-cross, and four
external-trade-divergence probes (E07, E09, E24, E26). Local Python and Rust
agreed 29/29; the official IMC comparison is still pending.

v2 drills *inside* the fill rather than *around* it. The hypothesis being
tested in each new probe is:

    > For an order that is intended to consume some part of the visible book,
    > does the official engine walk levels at each level's price, stop at
    > exactly the qty submitted, and ignore historical external trades as
    > liquidity? Or does it (a) blend prices, (b) over-fill from same-tick
    > external trades, (c) split fills weirdly across multiple submitted
    > orders?

The new battery covers volume boundaries (qty straddling level-1, level-2,
level-3 cuts), price granularity (price set above the touch but only enough
to cross level 1), order multiplicity (one big order vs many small orders
at the same price), price-priority within a single tick's submission batch,
near-touch resting (one-tick inside spread vs at touch vs one-tick away),
cross-product independence, and tick-by-tick continuity.

Output contract
---------------
Same as v1: each probe emits exactly one line per fire event in the form

    PROBE eid=G01 ts=1000 product=HYDROGEL_PACK action=BUY orders=10027x12 \\
        book=b=10018x8,...|a=10027x12,10030x13,... pos_before=0 limit=200 \\
        note=fill_at_l1_exact_l1vol=12

A schedule helper at the bottom of this file (`PROBE_SCHEDULE_V2`) can be
copy-pasted into `scripts/probe_analyze.py` so the diff harness can slice
fills per eid for v2 the same way it does for v1.

Safety
------
- Every probe self-flattens by its declared cleanup tick.
- Cleanup tick = probe_ts + 50 for single-shot probes; immediately after the
  range end for range probes.
- HYDROGEL probes never request more than 100 units at once (HYDROGEL limit
  is 200; flattens need 100 of room).
- VEV_6500 probes are bounded the same way relative to its 300 limit.
- All probes use integer prices and integer quantities.
- The trader is pure: no globals, no file I/O, no randomness.
- Returns (orders, conversions, traderData) every tick — submission safe.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState, Trade


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

H = "HYDROGEL_PACK"          # limit 200, deep multi-level book
VE = "VELVETFRUIT_EXTRACT"   # limit 200
VEV65 = "VEV_6500"           # limit 300, cheap (mid ~0.5)
VEV60 = "VEV_6000"           # limit 300, cheap

POS_LIMITS = {
    H: 200,
    VE: 200,
    VEV65: 300,
    VEV60: 300,
}

SCHEMA_VERSION = 2


# ---------------------------------------------------------------------------
# Probe schedule.
#
# 10000-tick day, partitioned into clean sections with idle anchors at the
# boundaries. Every active probe has an immediately-following AUTO_FLAT.
# Spare ticks (uncommitted) sit between sections so a slip in one section
# can't bleed into the next.
# ---------------------------------------------------------------------------

PROBES: List[Dict] = [
    # =======================================================================
    # Anchors
    # =======================================================================
    {"eid": "G00_IDLE_A",     "mode": "range", "start": 0,    "end": 499},

    # =======================================================================
    # Section A — volume granularity (HYDROGEL).
    # Same product, same crossing-style price; vary qty across level boundaries.
    # =======================================================================
    {"eid": "G01_FILL_L1_EXACT",   "mode": "single_ts", "ts": 1000, "product": H, "side": "BUY", "mode2": "vol_l1_exact"},
    {"eid": "G01_FLAT",            "mode": "single_ts", "ts": 1050, "product": H, "side": "AUTO_FLAT"},

    {"eid": "G02_FILL_L1_MINUS1",  "mode": "single_ts", "ts": 1100, "product": H, "side": "BUY", "mode2": "vol_l1_minus1"},
    {"eid": "G02_FLAT",            "mode": "single_ts", "ts": 1150, "product": H, "side": "AUTO_FLAT"},

    {"eid": "G03_FILL_L1_PLUS1",   "mode": "single_ts", "ts": 1200, "product": H, "side": "BUY", "mode2": "vol_l1_plus1"},
    {"eid": "G03_FLAT",            "mode": "single_ts", "ts": 1250, "product": H, "side": "AUTO_FLAT"},

    {"eid": "G04_FILL_L2_PARTIAL", "mode": "single_ts", "ts": 1300, "product": H, "side": "BUY", "mode2": "vol_l2_partial"},
    {"eid": "G04_FLAT",            "mode": "single_ts", "ts": 1350, "product": H, "side": "AUTO_FLAT"},

    {"eid": "G05_FILL_SUM2_EXACT", "mode": "single_ts", "ts": 1400, "product": H, "side": "BUY", "mode2": "vol_sum2_exact"},
    {"eid": "G05_FLAT",            "mode": "single_ts", "ts": 1450, "product": H, "side": "AUTO_FLAT"},

    {"eid": "G06_FILL_L3_TOUCH",   "mode": "single_ts", "ts": 1500, "product": H, "side": "BUY", "mode2": "vol_l3_touch"},
    {"eid": "G06_FLAT",            "mode": "single_ts", "ts": 1550, "product": H, "side": "AUTO_FLAT"},

    {"eid": "G07_FILL_SUM3_EXACT", "mode": "single_ts", "ts": 1600, "product": H, "side": "BUY", "mode2": "vol_sum3_exact"},
    {"eid": "G07_FLAT",            "mode": "single_ts", "ts": 1650, "product": H, "side": "AUTO_FLAT"},

    {"eid": "G08_FILL_OVERSHOOT5", "mode": "single_ts", "ts": 1700, "product": H, "side": "BUY", "mode2": "vol_overshoot", "excess": 5},
    {"eid": "G08_FLAT",            "mode": "single_ts", "ts": 1750, "product": H, "side": "AUTO_FLAT"},

    # =======================================================================
    # Section B — price granularity (HYDROGEL).
    # qty=1 always; vary price relative to the visible book. The expectation
    # under a "match at order.price" engine: each fills 1 unit at best_ask.
    # =======================================================================
    {"eid": "G10_PRICE_AT_TOP",    "mode": "single_ts", "ts": 2000, "product": H, "side": "BUY", "mode2": "price_at_top",   "qty": 1},
    {"eid": "G10_FLAT",            "mode": "single_ts", "ts": 2050, "product": H, "side": "AUTO_FLAT"},

    {"eid": "G11_PRICE_TOP_PLUS1", "mode": "single_ts", "ts": 2100, "product": H, "side": "BUY", "mode2": "price_above",    "qty": 1, "above_by": 1},
    {"eid": "G11_FLAT",            "mode": "single_ts", "ts": 2150, "product": H, "side": "AUTO_FLAT"},

    {"eid": "G12_PRICE_TOP_PLUS5", "mode": "single_ts", "ts": 2200, "product": H, "side": "BUY", "mode2": "price_above",    "qty": 1, "above_by": 5},
    {"eid": "G12_FLAT",            "mode": "single_ts", "ts": 2250, "product": H, "side": "AUTO_FLAT"},

    {"eid": "G13_PRICE_AT_L2",     "mode": "single_ts", "ts": 2300, "product": H, "side": "BUY", "mode2": "price_at_level", "qty": 1, "level": 2},
    {"eid": "G13_FLAT",            "mode": "single_ts", "ts": 2350, "product": H, "side": "AUTO_FLAT"},

    {"eid": "G14_PRICE_AT_L3",     "mode": "single_ts", "ts": 2400, "product": H, "side": "BUY", "mode2": "price_at_level", "qty": 1, "level": 3},
    {"eid": "G14_FLAT",            "mode": "single_ts", "ts": 2450, "product": H, "side": "AUTO_FLAT"},

    # G15: SELL mirror at best_bid, qty 1, to confirm sell-side basics.
    {"eid": "G15_PRICE_AT_BID",    "mode": "single_ts", "ts": 2500, "product": H, "side": "SELL", "mode2": "price_at_top",  "qty": 1},
    {"eid": "G15_FLAT",            "mode": "single_ts", "ts": 2550, "product": H, "side": "AUTO_FLAT"},

    # =======================================================================
    # Section C — order multiplicity.
    # All on HYDROGEL at same crossing price. Compare 1 big vs N small.
    # =======================================================================
    {"eid": "G20_MULTI_5x1",       "mode": "single_ts", "ts": 3000, "product": H, "side": "BUY", "mode2": "multi_singles", "n": 5, "qty_each": 1},
    {"eid": "G20_FLAT",            "mode": "single_ts", "ts": 3050, "product": H, "side": "AUTO_FLAT"},

    {"eid": "G21_MULTI_1x5",       "mode": "single_ts", "ts": 3100, "product": H, "side": "BUY", "mode2": "multi_one",    "qty": 5},
    {"eid": "G21_FLAT",            "mode": "single_ts", "ts": 3150, "product": H, "side": "AUTO_FLAT"},

    # G22: ladder at best_ask, +1, +2 — all 3 should fill at best_ask if engine
    # walks aggressive-first.
    {"eid": "G22_LADDER_ABOVE",    "mode": "single_ts", "ts": 3200, "product": H, "side": "BUY", "mode2": "ladder_above"},
    {"eid": "G22_FLAT",            "mode": "single_ts", "ts": 3250, "product": H, "side": "AUTO_FLAT"},

    # G23: BUY at best_ask AND SELL at best_bid in same tick. Same product.
    # Both should fill independently against the external book.
    {"eid": "G23_BOTH_SIDES",      "mode": "single_ts", "ts": 3300, "product": H, "side": "BOTH_SIDES", "qty": 1},
    {"eid": "G23_FLAT",            "mode": "single_ts", "ts": 3350, "product": H, "side": "AUTO_FLAT"},

    # G24: same-side, different prices, partial-fill mix. BUY at best_ask qty
    # = level1_vol AND BUY at best_ask+5 qty 1. Tests price-priority within
    # the same submitted batch when both can cross.
    {"eid": "G24_MIXED_AGGR",      "mode": "single_ts", "ts": 3400, "product": H, "side": "BUY", "mode2": "mixed_aggr"},
    {"eid": "G24_FLAT",            "mode": "single_ts", "ts": 3450, "product": H, "side": "AUTO_FLAT"},

    # =======================================================================
    # Section D — touch / inside-spread resting (range probes).
    # Each range is 100 ticks. Resting prices to compare against v1's ±1
    # offset probes:
    #   G30 = at best_bid (no offset)         -- baseline join-bid
    #   G31 = at best_bid + 1 (one-inside)    -- resting in spread above v1 E10
    #   G32 = at best_ask (sell-side join)
    #   G33 = at best_ask - 1 (improve ask)
    #   G34 = BUY at midprice                 -- mid-rest test
    # =======================================================================
    {"eid": "G30_REST_AT_BB",      "mode": "range", "start": 4000, "end": 4099, "product": VE, "side": "BUY",  "mode2": "rest_at_touch", "qty": 5},
    {"eid": "G30_FLAT",            "mode": "single_ts", "ts": 4100, "product": VE, "side": "AUTO_FLAT"},

    {"eid": "G31_REST_BB_PLUS1",   "mode": "range", "start": 4150, "end": 4249, "product": VE, "side": "BUY",  "mode2": "rest_inside_spread", "qty": 5, "offset": 1},
    {"eid": "G31_FLAT",            "mode": "single_ts", "ts": 4250, "product": VE, "side": "AUTO_FLAT"},

    {"eid": "G32_REST_AT_BA",      "mode": "range", "start": 4300, "end": 4399, "product": VE, "side": "SELL", "mode2": "rest_at_touch", "qty": 5},
    {"eid": "G32_FLAT",            "mode": "single_ts", "ts": 4400, "product": VE, "side": "AUTO_FLAT"},

    {"eid": "G33_REST_BA_MINUS1",  "mode": "range", "start": 4450, "end": 4549, "product": VE, "side": "SELL", "mode2": "rest_inside_spread", "qty": 5, "offset": 1},
    {"eid": "G33_FLAT",            "mode": "single_ts", "ts": 4550, "product": VE, "side": "AUTO_FLAT"},

    {"eid": "G34_REST_AT_MID",     "mode": "range", "start": 4600, "end": 4699, "product": VE, "side": "BUY",  "mode2": "rest_at_mid", "qty": 5},
    {"eid": "G34_FLAT",            "mode": "single_ts", "ts": 4700, "product": VE, "side": "AUTO_FLAT"},

    # =======================================================================
    # Section E — cross-product independence + tick continuity.
    # =======================================================================
    # G40: BUY 1 @ HYDROGEL best_ask AND BUY 1 @ VEV_6500 best_ask in same
    # tick. If the engine processes products independently (it should), both
    # fill. Failure mode: per-tick budget or weird global throttle.
    {"eid": "G40_CROSS_PRODUCT",   "mode": "single_ts", "ts": 5000, "product": H,     "side": "CROSS_PRODUCT"},
    {"eid": "G40_FLAT_H",          "mode": "single_ts", "ts": 5050, "product": H,     "side": "AUTO_FLAT"},
    {"eid": "G40_FLAT_V",          "mode": "single_ts", "ts": 5100, "product": VEV65, "side": "AUTO_FLAT"},

    # G50: same BUY 1 @ best_ask on HYDROGEL fired on three consecutive
    # ticks (no resting carry — IMC orders are single-tick). Each tick should
    # produce exactly one fill if level-1 has volume each time.
    {"eid": "G50_CONSEC_TICK_0",   "mode": "single_ts", "ts": 5200, "product": H, "side": "BUY", "mode2": "price_at_top", "qty": 1},
    {"eid": "G50_CONSEC_TICK_1",   "mode": "single_ts", "ts": 5201, "product": H, "side": "BUY", "mode2": "price_at_top", "qty": 1},
    {"eid": "G50_CONSEC_TICK_2",   "mode": "single_ts", "ts": 5202, "product": H, "side": "BUY", "mode2": "price_at_top", "qty": 1},
    {"eid": "G50_FLAT",            "mode": "single_ts", "ts": 5300, "product": H, "side": "AUTO_FLAT"},

    # G51: resting BUY at best_bid for 100 ticks, but resubmitted EVERY tick
    # so it's a fresh order. Compare fill rate vs v1 E10 (200 ticks at the
    # same setup). Differential should be zero per-tick — sanity check that
    # ranges don't bias the analyzer.
    {"eid": "G51_REST_RESUB",      "mode": "range", "start": 5400, "end": 5499, "product": H, "side": "BUY", "mode2": "rest_at_touch", "qty": 1},
    {"eid": "G51_FLAT",            "mode": "single_ts", "ts": 5500, "product": H, "side": "AUTO_FLAT"},

    # =======================================================================
    # Section F — phantom-liquidity stress (companion to v1 E07/E09/E26).
    # Tighter and longer than v1: more ticks, smaller offsets, bigger qty.
    # If "all" mode locally vs "none"-equivalent officially, this section is
    # where the divergence will be loudest.
    # =======================================================================
    # G60: BUY 1 @ best_bid - 5 (5 ticks below). Far below the touch but
    # still inside what historical external trades occasionally print at.
    {"eid": "G60_REST_BB_MINUS5",  "mode": "range", "start": 6000, "end": 6299, "product": VE, "side": "BUY",  "mode2": "rest_offset", "qty": 5, "offset": 5},
    {"eid": "G60_FLAT",            "mode": "single_ts", "ts": 6300, "product": VE, "side": "AUTO_FLAT"},

    # G61: SELL at best_ask + 5 mirror.
    {"eid": "G61_REST_BA_PLUS5",   "mode": "range", "start": 6350, "end": 6649, "product": VE, "side": "SELL", "mode2": "rest_offset", "qty": 5, "offset": 5},
    {"eid": "G61_FLAT",            "mode": "single_ts", "ts": 6650, "product": VE, "side": "AUTO_FLAT"},

    # G62: HYDROGEL wide-quote, ±10 from mid, 300 ticks. Stronger than v1 E26
    # which used offset 15 with only 500 ticks of qty=3. Here qty=5 to amplify.
    {"eid": "G62_WIDE_H_OFF10",    "mode": "range", "start": 7000, "end": 7299, "product": H,  "side": "WIDE_QUOTE", "offset": 10, "qty": 5},
    {"eid": "G62_FLAT",            "mode": "single_ts", "ts": 7300, "product": H,  "side": "AUTO_FLAT"},

    # =======================================================================
    # Section G — schema / engine edges not covered by v1.
    # =======================================================================
    # G70: BUY at extremely large negative price. Should be rejected or never
    # cross. Tests price-validation bounds.
    {"eid": "G70_PRICE_NEG",       "mode": "single_ts", "ts": 8000, "product": VEV65, "side": "BUY",  "mode2": "explicit_price", "price": -1, "qty": 1},
    {"eid": "G70_FLAT",            "mode": "single_ts", "ts": 8050, "product": VEV65, "side": "AUTO_FLAT"},

    # G71: huge qty (well above level depth). Tests that fills cap at book
    # depth instead of accepting the requested quantity.
    {"eid": "G71_QTY_HUGE",        "mode": "single_ts", "ts": 8100, "product": VEV65, "side": "BUY",  "mode2": "qty_huge"},
    {"eid": "G71_FLAT",            "mode": "single_ts", "ts": 8150, "product": VEV65, "side": "AUTO_FLAT"},

    # G72: SELL with qty larger than cap on the short side. VEV_6500 limit
    # is 300, we'll attempt -301. Companion to v1 E12 but on sell side.
    {"eid": "G72_SHORT_OVER",      "mode": "single_ts", "ts": 8200, "product": VEV65, "side": "SELL", "mode2": "short_overlimit"},
    {"eid": "G72_FLAT",            "mode": "single_ts", "ts": 8250, "product": VEV65, "side": "AUTO_FLAT"},

    # G73: cross-tick partial fill rebuild. Tick T: BUY huge qty at best_ask
    # (will only fill level-1 worth). Tick T+1: same BUY again (does the
    # engine treat this as the leftover from T or a fresh order?).
    {"eid": "G73_PARTIAL_CARRY_0", "mode": "single_ts", "ts": 8300, "product": H, "side": "BUY", "mode2": "vol_l1_plus1"},
    {"eid": "G73_PARTIAL_CARRY_1", "mode": "single_ts", "ts": 8301, "product": H, "side": "BUY", "mode2": "vol_l1_plus1"},
    {"eid": "G73_FLAT",            "mode": "single_ts", "ts": 8400, "product": H, "side": "AUTO_FLAT"},

    # =======================================================================
    # End-of-day idle anchor.
    # =======================================================================
    {"eid": "G99_IDLE_END",        "mode": "range", "start": 9500, "end": 9999},
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
# Helpers (mirror v1's structure so probe_analyze.py parses the lines
# identically).
# ---------------------------------------------------------------------------

def _fmt_levels(levels: List[Tuple[int, int]]) -> str:
    return ",".join(f"{p}x{abs(q)}" for p, q in levels)


def _depth_snapshot(od: Optional[OrderDepth]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
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


def _log(eid: str, ts: int, product: str, action: str, price, qty, od: Optional[OrderDepth], pos_before: int, note: str = "") -> None:
    limit = POS_LIMITS.get(product, -1)
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
    return [Order(product, int(price), int(qty)) for price, qty in items if qty != 0]


def _flatten_to_zero(product: str, od: Optional[OrderDepth], pos: int, eid: str, ts: int) -> List[Order]:
    if pos == 0 or od is None:
        _log(eid, ts, product, "FLAT_NOOP", 0, 0, od, pos, note="already_flat_or_no_book")
        return []
    if pos > 0:
        bb, _ = _best_bid_ask(od)
        if bb is None:
            _log(eid, ts, product, "FLAT_NO_BID", 0, 0, od, pos, note="no_bid_to_hit")
            return []
        orders = [(bb - 1, -pos)]
        _log(eid, ts, product, "FLAT_SELL", bb - 1, -pos, od, pos, note=f"target_flat_{pos}")
        return _emit_orders(product, orders)
    _, ba = _best_bid_ask(od)
    if ba is None:
        _log(eid, ts, product, "FLAT_NO_ASK", 0, 0, od, pos, note="no_ask_to_lift")
        return []
    orders = [(ba + 1, -pos)]
    _log(eid, ts, product, "FLAT_BUY", ba + 1, -pos, od, pos, note=f"target_flat_{pos}")
    return _emit_orders(product, orders)


# ---------------------------------------------------------------------------
# Volume-granularity dispatch (Section A) — sized relative to live book depth.
# ---------------------------------------------------------------------------

def _vol_probe_qty_price(mode2: str, asks: List[Tuple[int, int]], extra: Dict) -> Tuple[Optional[int], Optional[int], str]:
    """Return (price, qty, note) for one of the volume-granularity modes, or
    (None, None, reason) if the live book is too thin to run the probe.

    The price is set so the order CAN cross the relevant level(s); the engine
    decides where the actual fills land.
    """
    if not asks:
        return None, None, "no_ask"
    l1p, l1v = asks[0]
    l2p, l2v = (asks[1] if len(asks) > 1 else (l1p, 0))
    l3p, l3v = (asks[2] if len(asks) > 2 else (l2p, 0))

    if mode2 == "vol_l1_exact":
        qty = l1v
        return l1p, qty, f"l1_exact_l1vol={l1v}"
    if mode2 == "vol_l1_minus1":
        qty = max(1, l1v - 1)
        return l1p, qty, f"l1_minus1_l1vol={l1v}_qty={qty}"
    if mode2 == "vol_l1_plus1":
        if l2v <= 0:
            return None, None, "no_l2"
        qty = l1v + 1
        return l2p, qty, f"l1_plus1_l1vol={l1v}_target_l2={l2p}"
    if mode2 == "vol_l2_partial":
        if l2v <= 0:
            return None, None, "no_l2"
        qty = l1v + max(1, l2v // 2)
        return l2p, qty, f"l2_partial_l1={l1v}_l2={l2v}_qty={qty}"
    if mode2 == "vol_sum2_exact":
        if l2v <= 0:
            return None, None, "no_l2"
        qty = l1v + l2v
        return l2p, qty, f"sum2_l1={l1v}_l2={l2v}"
    if mode2 == "vol_l3_touch":
        if l3v <= 0:
            return None, None, "no_l3"
        qty = l1v + l2v + min(2, l3v)
        return l3p, qty, f"l3_touch_l1={l1v}_l2={l2v}_l3={l3v}_qty={qty}"
    if mode2 == "vol_sum3_exact":
        if l3v <= 0:
            return None, None, "no_l3"
        qty = l1v + l2v + l3v
        return l3p, qty, f"sum3_l1={l1v}_l2={l2v}_l3={l3v}"
    if mode2 == "vol_overshoot":
        if l3v <= 0:
            return None, None, "no_l3"
        excess = int(extra.get("excess", 5))
        qty = l1v + l2v + l3v + excess
        return l3p + 50, qty, f"overshoot_sum3_plus_{excess}_qty={qty}"
    return None, None, f"unknown_vol_mode={mode2}"


# ---------------------------------------------------------------------------
# Core dispatch
# ---------------------------------------------------------------------------

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

    bids, asks = _depth_snapshot(od)
    bb, ba = _best_bid_ask(od)

    # ---- Section A: volume granularity -----------------------------------
    if mode2.startswith("vol_"):
        if not asks:
            _log(eid, ts, product, "SKIP_NO_ASK", 0, 0, od, pos)
            return []
        price, qty, note = _vol_probe_qty_price(mode2, asks, probe)
        if qty is None or qty <= 0:
            _log(eid, ts, product, "SKIP_THIN_BOOK", 0, 0, od, pos, note=note)
            return []
        # Respect position limit.
        limit = POS_LIMITS.get(product, 100)
        room = limit - pos
        # Reserve enough room for cleanup-on-the-next-tick. HYDROGEL flatten
        # walks 1 tick below best_bid so we don't need extra book reservation,
        # but we do need pos+qty <= limit.
        if qty > room:
            _log(eid, ts, product, "SKIP_NO_ROOM", 0, 0, od, pos, note=f"qty={qty}_room={room}_{note}")
            return []
        _log(eid, ts, product, "BUY", price, qty, od, pos, note=note)
        return _emit_orders(product, [(price, qty)])

    # ---- Section B: price granularity ------------------------------------
    if mode2 == "price_at_top":
        qty = int(probe.get("qty", 1))
        if side == "BUY":
            if ba is None:
                _log(eid, ts, product, "SKIP_NO_ASK", 0, 0, od, pos)
                return []
            _log(eid, ts, product, "BUY", ba, qty, od, pos, note="price_at_top")
            return _emit_orders(product, [(ba, qty)])
        if side == "SELL":
            if bb is None:
                _log(eid, ts, product, "SKIP_NO_BID", 0, 0, od, pos)
                return []
            _log(eid, ts, product, "SELL", bb, -qty, od, pos, note="price_at_top")
            return _emit_orders(product, [(bb, -qty)])

    if mode2 == "price_above":
        qty = int(probe.get("qty", 1))
        above_by = int(probe.get("above_by", 1))
        if side == "BUY":
            if ba is None:
                _log(eid, ts, product, "SKIP_NO_ASK", 0, 0, od, pos)
                return []
            price = ba + above_by
            _log(eid, ts, product, "BUY", price, qty, od, pos, note=f"above_top_by_{above_by}")
            return _emit_orders(product, [(price, qty)])

    if mode2 == "price_at_level":
        qty = int(probe.get("qty", 1))
        level = int(probe.get("level", 2))
        if not asks or len(asks) < level:
            _log(eid, ts, product, "SKIP_THIN_BOOK", 0, 0, od, pos, note=f"need_level_{level}")
            return []
        price = asks[level - 1][0]
        _log(eid, ts, product, "BUY", price, qty, od, pos, note=f"price_at_l{level}")
        return _emit_orders(product, [(price, qty)])

    # ---- Section C: order multiplicity -----------------------------------
    if mode2 == "multi_singles":
        if ba is None:
            _log(eid, ts, product, "SKIP_NO_ASK", 0, 0, od, pos)
            return []
        n = int(probe.get("n", 5))
        qty_each = int(probe.get("qty_each", 1))
        items = [(ba, qty_each) for _ in range(n)]
        _log(eid, ts, product, "BUY_MULTI", items, 0, od, pos, note=f"n={n}_qty_each={qty_each}")
        return _emit_orders(product, items)

    if mode2 == "multi_one":
        if ba is None:
            _log(eid, ts, product, "SKIP_NO_ASK", 0, 0, od, pos)
            return []
        qty = int(probe.get("qty", 5))
        _log(eid, ts, product, "BUY", ba, qty, od, pos, note=f"single_qty={qty}")
        return _emit_orders(product, [(ba, qty)])

    if mode2 == "ladder_above":
        if ba is None:
            _log(eid, ts, product, "SKIP_NO_ASK", 0, 0, od, pos)
            return []
        # 3 BUYs at best_ask, +1, +2; qty 1 each.
        items = [(ba, 1), (ba + 1, 1), (ba + 2, 1)]
        _log(eid, ts, product, "BUY_LADDER", items, 0, od, pos, note="ba,ba+1,ba+2")
        return _emit_orders(product, items)

    if side == "BOTH_SIDES":
        if bb is None or ba is None:
            _log(eid, ts, product, "SKIP_NO_TOUCH", 0, 0, od, pos)
            return []
        qty = int(probe.get("qty", 1))
        items = [(ba, qty), (bb, -qty)]
        _log(eid, ts, product, "BUY_AND_SELL", items, 0, od, pos, note="independent_sides")
        return _emit_orders(product, items)

    if mode2 == "mixed_aggr":
        if ba is None or not asks:
            _log(eid, ts, product, "SKIP_NO_ASK", 0, 0, od, pos)
            return []
        l1v = asks[0][1]
        # First order eats level 1; second order is more aggressive (price
        # +5) but tiny — both should cross. Tests price-priority within batch.
        items = [(ba, l1v), (ba + 5, 1)]
        limit = POS_LIMITS.get(product, 100)
        if pos + l1v + 1 > limit:
            _log(eid, ts, product, "SKIP_NO_ROOM", 0, 0, od, pos, note=f"l1v={l1v}_room={limit - pos}")
            return []
        _log(eid, ts, product, "BUY_MIXED", items, 0, od, pos, note=f"eat_l1_{l1v}+1_at_ba+5")
        return _emit_orders(product, items)

    # ---- Section D: resting probes ---------------------------------------
    if mode2 == "rest_at_touch":
        qty = int(probe.get("qty", 5))
        if side == "BUY":
            if bb is None:
                return []
            limit = POS_LIMITS.get(product, 100)
            if pos + qty > limit:
                return []
            if ts % 50 == 0:
                _log(eid, ts, product, "BUY_RESTING", bb, qty, od, pos, note="at_best_bid")
            return _emit_orders(product, [(bb, qty)])
        if side == "SELL":
            if ba is None:
                return []
            limit = POS_LIMITS.get(product, 100)
            if pos - qty < -limit:
                return []
            if ts % 50 == 0:
                _log(eid, ts, product, "SELL_RESTING", ba, -qty, od, pos, note="at_best_ask")
            return _emit_orders(product, [(ba, -qty)])

    if mode2 == "rest_inside_spread":
        qty = int(probe.get("qty", 5))
        offset = int(probe.get("offset", 1))
        if side == "BUY":
            if bb is None or ba is None or ba - bb <= offset:
                # Spread too tight: bb+offset would cross. Skip.
                if ts % 50 == 0:
                    _log(eid, ts, product, "SKIP_TIGHT_SPREAD", 0, 0, od, pos, note=f"spread<={offset}")
                return []
            price = bb + offset
            limit = POS_LIMITS.get(product, 100)
            if pos + qty > limit:
                return []
            if ts % 50 == 0:
                _log(eid, ts, product, "BUY_RESTING", price, qty, od, pos, note=f"bb_plus_{offset}")
            return _emit_orders(product, [(price, qty)])
        if side == "SELL":
            if bb is None or ba is None or ba - bb <= offset:
                if ts % 50 == 0:
                    _log(eid, ts, product, "SKIP_TIGHT_SPREAD", 0, 0, od, pos, note=f"spread<={offset}")
                return []
            price = ba - offset
            limit = POS_LIMITS.get(product, 100)
            if pos - qty < -limit:
                return []
            if ts % 50 == 0:
                _log(eid, ts, product, "SELL_RESTING", price, -qty, od, pos, note=f"ba_minus_{offset}")
            return _emit_orders(product, [(price, -qty)])

    if mode2 == "rest_at_mid":
        qty = int(probe.get("qty", 5))
        if bb is None or ba is None:
            return []
        # Use floor mid; Prosperity prices are integers.
        mid = (bb + ba) // 2
        if mid <= bb or mid >= ba:
            # Mid coincides with touch in 1-tick spread; would cross. Skip.
            if ts % 50 == 0:
                _log(eid, ts, product, "SKIP_MID_AT_TOUCH", mid, 0, od, pos, note=f"bb={bb}_ba={ba}")
            return []
        limit = POS_LIMITS.get(product, 100)
        if side == "BUY":
            if pos + qty > limit:
                return []
            if ts % 50 == 0:
                _log(eid, ts, product, "BUY_RESTING", mid, qty, od, pos, note="at_mid")
            return _emit_orders(product, [(mid, qty)])

    if mode2 == "rest_offset":
        qty = int(probe.get("qty", 5))
        offset = int(probe.get("offset", 5))
        if side == "BUY":
            if bb is None:
                return []
            price = bb - offset
            limit = POS_LIMITS.get(product, 100)
            if pos + qty > limit:
                return []
            if ts % 50 == 0:
                _log(eid, ts, product, "BUY_RESTING", price, qty, od, pos, note=f"bb_minus_{offset}")
            return _emit_orders(product, [(price, qty)])
        if side == "SELL":
            if ba is None:
                return []
            price = ba + offset
            limit = POS_LIMITS.get(product, 100)
            if pos - qty < -limit:
                return []
            if ts % 50 == 0:
                _log(eid, ts, product, "SELL_RESTING", price, -qty, od, pos, note=f"ba_plus_{offset}")
            return _emit_orders(product, [(price, -qty)])

    # ---- Section E special sides -----------------------------------------
    if side == "CROSS_PRODUCT":
        # Hits two products in one tick. Returns orders for BOTH; the caller
        # merges by symbol so this is safe even though `product` is set to H.
        out: List[Order] = []
        if ba is not None:
            _log(eid, ts, H, "BUY", ba, 1, od, pos, note="hydrogel_at_top")
            out.append(Order(H, int(ba), 1))
        # And on VEV_6500.
        v_od = state.order_depths.get(VEV65)
        v_bids, v_asks = _depth_snapshot(v_od)
        v_pos = state.position.get(VEV65, 0)
        if v_asks:
            v_ba = v_asks[0][0]
            _log(eid, ts, VEV65, "BUY", v_ba, 1, v_od, v_pos, note="vev_at_top")
            out.append(Order(VEV65, int(v_ba), 1))
        return out

    # ---- Section F wide quote (reused name from v1 for clarity) ---------
    if side == "WIDE_QUOTE":
        if bb is None or ba is None:
            return []
        offset = int(probe.get("offset", 10))
        qty = int(probe.get("qty", 5))
        limit = POS_LIMITS.get(product, 100)
        items: List[Tuple[int, int]] = []
        if pos + qty <= limit:
            items.append((bb - offset, qty))
        if pos - qty >= -limit:
            items.append((ba + offset, -qty))
        if ts % 50 == 0:
            _log(eid, ts, product, "WIDE_QUOTE", items, 0, od, pos, note=f"offset_{offset}")
        return _emit_orders(product, items)

    # ---- Section G schema edges ------------------------------------------
    if mode2 == "explicit_price":
        price = int(probe["price"])
        qty = int(probe.get("qty", 1))
        signed = qty if side == "BUY" else -qty
        _log(eid, ts, product, side, price, signed, od, pos, note=f"explicit_price_{price}")
        return _emit_orders(product, [(price, signed)])

    if mode2 == "qty_huge":
        # BUY qty 999 at a high crossing price. Should fill only what the
        # book can support.
        if not asks:
            _log(eid, ts, product, "SKIP_NO_ASK", 0, 0, od, pos)
            return []
        price = asks[-1][0] + 100
        # Cap at room-to-limit so we don't violate.
        limit = POS_LIMITS.get(product, 100)
        room = limit - pos
        qty = min(999, max(1, room))
        _log(eid, ts, product, "BUY", price, qty, od, pos, note=f"qty_huge_{qty}")
        return _emit_orders(product, [(price, qty)])

    if mode2 == "short_overlimit":
        # SELL qty = limit + 1 at extremely low price (crossing). Engine
        # should reject all orders for this product this tick (matches v1
        # E12 behavior on the buy side).
        if bb is None:
            _log(eid, ts, product, "SKIP_NO_BID", 0, 0, od, pos)
            return []
        limit = POS_LIMITS.get(product, 100)
        qty = limit + 1 + pos  # +pos accounts for any existing long
        _log(eid, ts, product, "SELL", bb, -qty, od, pos, note=f"short_over_limit_by_1")
        return _emit_orders(product, [(bb, -qty)])

    # Unknown shape — log & skip.
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
            for o in _run_single_probe(probe, state):
                orders.setdefault(o.symbol, []).append(o)

        # 2) Range probes.
        for probe in _RANGE_PROBES:
            if probe["mode"] != "range":
                continue
            if ts < int(probe["start"]) or ts > int(probe["end"]):
                continue
            if probe.get("side") is None:
                if ts == int(probe["start"]) or ts == int(probe["end"]):
                    print(f"PROBE eid={probe['eid']} ts={ts} product=NONE action=IDLE_MARK")
                continue
            for o in _run_single_probe(probe, state):
                orders.setdefault(o.symbol, []).append(o)

        trader_data = json.dumps({"schema": SCHEMA_VERSION, "ts": ts})
        return orders, 0, trader_data


# ---------------------------------------------------------------------------
# Schedule export — copy this list into scripts/probe_analyze.py as
# `PROBE_SCHEDULE_V2` so the diff harness can slice fills per eid.
#
# Only entries that need fill aggregation (non-flatten, non-noop) are listed.
# Flatten ticks are intentionally omitted — they're cleanup, not experiments.
# ---------------------------------------------------------------------------

PROBE_SCHEDULE_V2: List[Dict] = [
    {"eid": "G00_IDLE_A",          "mode": "range", "start": 0, "end": 499, "product": None},

    {"eid": "G01_FILL_L1_EXACT",   "mode": "single_ts", "ts": 1000, "product": H},
    {"eid": "G02_FILL_L1_MINUS1",  "mode": "single_ts", "ts": 1100, "product": H},
    {"eid": "G03_FILL_L1_PLUS1",   "mode": "single_ts", "ts": 1200, "product": H},
    {"eid": "G04_FILL_L2_PARTIAL", "mode": "single_ts", "ts": 1300, "product": H},
    {"eid": "G05_FILL_SUM2_EXACT", "mode": "single_ts", "ts": 1400, "product": H},
    {"eid": "G06_FILL_L3_TOUCH",   "mode": "single_ts", "ts": 1500, "product": H},
    {"eid": "G07_FILL_SUM3_EXACT", "mode": "single_ts", "ts": 1600, "product": H},
    {"eid": "G08_FILL_OVERSHOOT5", "mode": "single_ts", "ts": 1700, "product": H},

    {"eid": "G10_PRICE_AT_TOP",    "mode": "single_ts", "ts": 2000, "product": H},
    {"eid": "G11_PRICE_TOP_PLUS1", "mode": "single_ts", "ts": 2100, "product": H},
    {"eid": "G12_PRICE_TOP_PLUS5", "mode": "single_ts", "ts": 2200, "product": H},
    {"eid": "G13_PRICE_AT_L2",     "mode": "single_ts", "ts": 2300, "product": H},
    {"eid": "G14_PRICE_AT_L3",     "mode": "single_ts", "ts": 2400, "product": H},
    {"eid": "G15_PRICE_AT_BID",    "mode": "single_ts", "ts": 2500, "product": H},

    {"eid": "G20_MULTI_5x1",       "mode": "single_ts", "ts": 3000, "product": H},
    {"eid": "G21_MULTI_1x5",       "mode": "single_ts", "ts": 3100, "product": H},
    {"eid": "G22_LADDER_ABOVE",    "mode": "single_ts", "ts": 3200, "product": H},
    {"eid": "G23_BOTH_SIDES",      "mode": "single_ts", "ts": 3300, "product": H},
    {"eid": "G24_MIXED_AGGR",      "mode": "single_ts", "ts": 3400, "product": H},

    {"eid": "G30_REST_AT_BB",      "mode": "range", "start": 4000, "end": 4099, "product": VE},
    {"eid": "G31_REST_BB_PLUS1",   "mode": "range", "start": 4150, "end": 4249, "product": VE},
    {"eid": "G32_REST_AT_BA",      "mode": "range", "start": 4300, "end": 4399, "product": VE},
    {"eid": "G33_REST_BA_MINUS1",  "mode": "range", "start": 4450, "end": 4549, "product": VE},
    {"eid": "G34_REST_AT_MID",     "mode": "range", "start": 4600, "end": 4699, "product": VE},

    {"eid": "G40_CROSS_PRODUCT",   "mode": "single_ts", "ts": 5000, "product": None},  # multi-product
    {"eid": "G50_CONSEC_TICK_0",   "mode": "single_ts", "ts": 5200, "product": H},
    {"eid": "G50_CONSEC_TICK_1",   "mode": "single_ts", "ts": 5201, "product": H},
    {"eid": "G50_CONSEC_TICK_2",   "mode": "single_ts", "ts": 5202, "product": H},
    {"eid": "G51_REST_RESUB",      "mode": "range", "start": 5400, "end": 5499, "product": H},

    {"eid": "G60_REST_BB_MINUS5",  "mode": "range", "start": 6000, "end": 6299, "product": VE},
    {"eid": "G61_REST_BA_PLUS5",   "mode": "range", "start": 6350, "end": 6649, "product": VE},
    {"eid": "G62_WIDE_H_OFF10",    "mode": "range", "start": 7000, "end": 7299, "product": H},

    {"eid": "G70_PRICE_NEG",       "mode": "single_ts", "ts": 8000, "product": VEV65},
    {"eid": "G71_QTY_HUGE",        "mode": "single_ts", "ts": 8100, "product": VEV65},
    {"eid": "G72_SHORT_OVER",      "mode": "single_ts", "ts": 8200, "product": VEV65},
    {"eid": "G73_PARTIAL_CARRY_0", "mode": "single_ts", "ts": 8300, "product": H},
    {"eid": "G73_PARTIAL_CARRY_1", "mode": "single_ts", "ts": 8301, "product": H},

    {"eid": "G99_IDLE_END",        "mode": "range", "start": 9500, "end": 9999, "product": None},
]
