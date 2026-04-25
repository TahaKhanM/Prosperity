"""Prosperity 4 Round 3 — IMC matching-engine probe trader v2.

Purpose
=======
Pin down WHY the official IMC backtester emits multiple fill rows for a
single sweep order on VEV_6500 at the floor/ceiling price (observed in
v1: E13 BUY 17@1 -> 13@1 + 4@1; E15 SELL 16@0 -> 11@0 + 5@0), while
both our Python and Rust local backtesters emit a single coalesced fill.

Hypothesis under test
---------------------
IMC's matching engine, when a submission order consumes liquidity at a
given price level, splits the resulting fill across the *market_trades*
rows recorded at that same `(symbol, price, timestamp)` — treating each
trade row as one counterparty quote. Our locals only reach the
market_trades fallback after the book level is exhausted, and even then
they don't preserve per-row granularity.

If the hypothesis holds, then for a given probe BUY n@1 firing at tick T:

    n_official_fills(T, n) == count of trades-CSV rows
                              with symbol=VEV_6500, price=1, ts=T

Design
------
- Single product: VEV_6500. (Limit 300, deep-OTM, floor at 1, ceiling at 0.)
- Vary order qty across {1, 5, 11, 17, 30, 100, 250} — covers below
  typical level volume, equal to typical level volume, and well above.
- 4 samples per qty so the trades-CSV row distribution gets sampled.
- Probe at price=1 BUY (floor) is primary; one symmetric SELL series at
  price=0 confirms the rule isn't BUY-specific.
- Each probe is followed 100 ticks later by an AUTO_FLAT to clear
  position before the next probe — so we never run into the 300-position
  limit and probes don't contaminate each other.
- All probes within day 0 (ts < 10000).

Cross-checks built in
---------------------
- Repeating the same (qty, price) at distinct timestamps lets us
  distinguish "fill split is deterministic in qty alone" (would refute
  the hypothesis — split should vary with sample) from "fill split
  varies with the underlying trades-CSV state" (supports hypothesis).
- The SELL series confirms the rule applies symmetrically — a BUY-only
  asymmetry would be a different bug class.

Output contract (same as v1)
----------------------------
One PROBE line per event:

    PROBE eid=F03_BUY_q17_s0 ts=1800 product=VEV_6500 action=BUY \
        orders=1x17 book=b=...|a=... pos_before=0 limit=300 note=floor_buy

The companion `scripts/probe_analyze.py` parses these and joins them to
SUBMISSION fills from the local + official replays. The fill-shape
divergence flag (added in this same patch) will surface every
multi-row IMC fill that we don't reproduce.

Safety
------
- Pure: no globals (only schedule constants), no I/O, no randomness.
- Returns (orders, conversions, traderData) every tick.
- Position-limit aware: a probe is skipped if it would breach the limit
  (rather than silently truncated by the engine — we want clean attempts).
- AUTO_FLAT after every probe; final IDLE_END pads to end-of-day.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VEV65 = "VEV_6500"
POS_LIMIT_VEV65 = 300

SCHEMA_VERSION = 2

# Qty grid for BUY @ price=1 (floor / cheapest ask). 250 deliberately
# exceeds typical single-level volume so we observe what happens when
# the order has to sweep multiple levels OR fall through to the
# market_trades fallback.
BUY_QTYS: List[int] = [1, 5, 11, 17, 30, 100, 250]

# One symmetric SELL series at qty=17 (the v1 E13 split case) to
# confirm rule symmetry between buy / sell sides.
SELL_QTY: int = 17

# Samples per (side, qty). 4 distinct ts values per series so we
# observe variance in the underlying trades-CSV row count.
N_SAMPLES: int = 4

# Tick spacing: probe at ts=T, flatten at ts=T+100, next probe at T+200.
# Keeps probes well-separated so AUTO_FLAT always finishes before the
# next probe starts.
PROBE_SPACING: int = 200
FLAT_OFFSET: int = 100

# Day 0 ends at ts=9999. We start at ts=200 (after IDLE warmup) and want
# to finish well before 10000 so AUTO_FLAT always lands in-day.
WARMUP_END: int = 199


# ---------------------------------------------------------------------------
# Build schedule. Each entry is (eid, mode, ts/(start, end), action_kwargs).
# ---------------------------------------------------------------------------


def _build_schedule() -> List[Dict]:
    sched: List[Dict] = [
        # Long warm-up region with zero orders, so the engine has clean
        # internal state when the probes start. Also useful as a baseline
        # in the diff tool: any non-zero fills here = engine bug.
        {"eid": "F00_IDLE_WARMUP", "mode": "range", "start": 0, "end": WARMUP_END},
    ]

    eid_idx = 1
    ts = WARMUP_END + 1

    # ----- BUY series at price=1 (the floor ask, where stacking lives). -----
    for qty in BUY_QTYS:
        for sample in range(N_SAMPLES):
            sched.append(
                {
                    "eid": f"F{eid_idx:02d}_BUY_q{qty}_s{sample}",
                    "mode": "single_ts",
                    "ts": ts,
                    "product": VEV65,
                    "side": "BUY",
                    "mode2": "explicit_price",
                    "price": 1,
                    "qty": qty,
                    "note": f"floor_buy_qty{qty}_sample{sample}",
                }
            )
            eid_idx += 1
            sched.append(
                {
                    "eid": f"F{eid_idx:02d}_FLAT_after_BUY_q{qty}_s{sample}",
                    "mode": "single_ts",
                    "ts": ts + FLAT_OFFSET,
                    "product": VEV65,
                    "side": "AUTO_FLAT",
                    "note": f"flat_after_buy_qty{qty}_s{sample}",
                }
            )
            eid_idx += 1
            ts += PROBE_SPACING

    # ----- SELL series at price=0 (the floor bid). -----
    for sample in range(N_SAMPLES):
        sched.append(
            {
                "eid": f"F{eid_idx:02d}_SELL_q{SELL_QTY}_s{sample}",
                "mode": "single_ts",
                "ts": ts,
                "product": VEV65,
                "side": "SELL",
                "mode2": "explicit_price",
                "price": 0,
                "qty": SELL_QTY,
                "note": f"floor_sell_qty{SELL_QTY}_sample{sample}",
            }
        )
        eid_idx += 1
        sched.append(
            {
                "eid": f"F{eid_idx:02d}_FLAT_after_SELL_q{SELL_QTY}_s{sample}",
                "mode": "single_ts",
                "ts": ts + FLAT_OFFSET,
                "product": VEV65,
                "side": "AUTO_FLAT",
                "note": f"flat_after_sell_qty{SELL_QTY}_s{sample}",
            }
        )
        eid_idx += 1
        ts += PROBE_SPACING

    # ----- Final IDLE pad. -----
    sched.append({"eid": f"F{eid_idx:02d}_IDLE_END", "mode": "range", "start": ts, "end": 9999})
    return sched


PROBES: List[Dict] = _build_schedule()

# Pre-index for O(1) tick lookup.
_SINGLE_PROBES_BY_TS: Dict[int, List[Dict]] = {}
_RANGE_PROBES: List[Dict] = []
for _p in PROBES:
    if _p["mode"] == "single_ts":
        _SINGLE_PROBES_BY_TS.setdefault(int(_p["ts"]), []).append(_p)
    else:
        _RANGE_PROBES.append(_p)


# ---------------------------------------------------------------------------
# Book helpers (kept inline so this trader is self-contained / submission-safe).
# ---------------------------------------------------------------------------


def _depth_snapshot(
    od: Optional[OrderDepth],
) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """(bids_sorted_desc, asks_sorted_asc) as (price, positive_qty)."""
    if od is None:
        return [], []
    bids = sorted(((int(p), int(abs(q))) for p, q in od.buy_orders.items()), key=lambda x: -x[0])
    asks = sorted(((int(p), int(abs(q))) for p, q in od.sell_orders.items()), key=lambda x: x[0])
    return bids, asks


def _compact_book(od: Optional[OrderDepth]) -> str:
    bids, asks = _depth_snapshot(od)
    b = ",".join(f"{p}x{q}" for p, q in bids[:3]) if bids else "EMPTY"
    a = ",".join(f"{p}x{q}" for p, q in asks[:3]) if asks else "EMPTY"
    return f"b={b}|a={a}"


def _best_bid_ask(od: Optional[OrderDepth]) -> Tuple[Optional[int], Optional[int]]:
    bids, asks = _depth_snapshot(od)
    return (bids[0][0] if bids else None), (asks[0][0] if asks else None)


def _log(
    eid: str,
    ts: int,
    product: str,
    action: str,
    price,
    qty,
    od: Optional[OrderDepth],
    pos_before: int,
    note: str = "",
) -> None:
    if isinstance(price, list):
        pq = ",".join(f"{p}x{q}" for p, q in price)
    else:
        pq = f"{price}x{qty}"
    limit = POS_LIMIT_VEV65 if product == VEV65 else -1
    print(
        f"PROBE eid={eid} ts={ts} product={product} action={action} "
        f"orders={pq} book={_compact_book(od)} pos_before={pos_before} "
        f"limit={limit} note={note}"
    )


def _flatten(product: str, od: Optional[OrderDepth], pos: int, eid: str, ts: int) -> List[Order]:
    """Aggressive flatten — same shape as v1 so the diff tool's existing
    SUBMISSION-fill aggregator works without changes."""
    if pos == 0 or od is None:
        _log(eid, ts, product, "FLAT_NOOP", 0, 0, od, pos, note="already_flat_or_no_book")
        return []
    if pos > 0:
        bb, _ = _best_bid_ask(od)
        if bb is None:
            _log(eid, ts, product, "FLAT_NO_BID", 0, 0, od, pos, note="no_bid_to_hit")
            return []
        _log(eid, ts, product, "FLAT_SELL", bb - 1, -pos, od, pos, note=f"target_flat_{pos}")
        return [Order(product, int(bb - 1), int(-pos))]
    _, ba = _best_bid_ask(od)
    if ba is None:
        _log(eid, ts, product, "FLAT_NO_ASK", 0, 0, od, pos, note="no_ask_to_lift")
        return []
    _log(eid, ts, product, "FLAT_BUY", ba + 1, -pos, od, pos, note=f"target_flat_{pos}")
    return [Order(product, int(ba + 1), int(-pos))]


# ---------------------------------------------------------------------------
# Probe runner
# ---------------------------------------------------------------------------


def _run_single_probe(probe: Dict, state: TradingState) -> List[Order]:
    eid = probe["eid"]
    ts = state.timestamp
    product = probe["product"]
    side = probe["side"]
    od = state.order_depths.get(product)
    pos = state.position.get(product, 0)
    note = probe.get("note", "")

    if side == "AUTO_FLAT":
        return _flatten(product, od, pos, eid, ts)

    if probe.get("mode2") == "explicit_price":
        price = int(probe["price"])
        qty = int(probe["qty"])
        if side == "BUY":
            # Skip cleanly if it would breach the position limit.
            # Better to log a SKIP than to have the engine truncate it,
            # because truncation contaminates the splitting signal.
            if pos + qty > POS_LIMIT_VEV65:
                _log(eid, ts, product, "SKIP_POSLIMIT", price, qty, od, pos,
                     note=f"{note}_room={POS_LIMIT_VEV65 - pos}")
                return []
            _log(eid, ts, product, "BUY", price, qty, od, pos, note=note)
            return [Order(product, price, qty)]
        if side == "SELL":
            if pos - qty < -POS_LIMIT_VEV65:
                _log(eid, ts, product, "SKIP_POSLIMIT", price, -qty, od, pos,
                     note=f"{note}_room={pos + POS_LIMIT_VEV65}")
                return []
            _log(eid, ts, product, "SELL", price, -qty, od, pos, note=note)
            return [Order(product, price, -qty)]

    _log(eid, ts, product, "UNKNOWN_MODE", 0, 0, od, pos, note=f"side={side}")
    return []


# ---------------------------------------------------------------------------
# Trader entry point — submission-safe shape.
# ---------------------------------------------------------------------------


class Trader:
    def run(self, state: TradingState):
        ts = int(state.timestamp)
        orders: Dict[str, List[Order]] = {}

        for probe in _SINGLE_PROBES_BY_TS.get(ts, []):
            for o in _run_single_probe(probe, state):
                orders.setdefault(o.symbol, []).append(o)

        for probe in _RANGE_PROBES:
            if ts < int(probe["start"]) or ts > int(probe["end"]):
                continue
            # IDLE markers — log only at the boundary ticks to keep logs slim.
            if ts == int(probe["start"]) or ts == int(probe["end"]):
                print(f"PROBE eid={probe['eid']} ts={ts} product=NONE action=IDLE_MARK")

        trader_data = json.dumps({"schema": SCHEMA_VERSION, "ts": ts})
        return orders, 0, trader_data
