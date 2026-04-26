"""Round 4 Mark-observer (no orders; observation-only).

Reads the new Round 4 counterparty fields (`trade.buyer`, `trade.seller` ->
strings like `"Mark 14"`) and accumulates a per-(product, Mark) decaying
"lean" signal in `traderData`. Emits no orders. Useful for:

- Confirming the Rust backtester ingests counterparty IDs correctly (you
  should see non-`None` buyer/seller values in `combined.log`).
- Snapshotting the per-Mark signal evolution to compare against the offline
  EDA in `prosperity-research/03_eda/round4/headline_findings.md`.

The signal weights and the decay rate match the recommended starting
parameters in `prosperity-research/04_signal_notes/round4/counterparty_play_book.md`.

Once you are ready to *trade* on these signals, copy this file to
`round4_mark_lean_v01.py`, layer the R3 v15 trading logic on top, and skew
the MM fair / take threshold by `lean[product]` as described in
`prosperity-research/08_playbooks/round4_strategy_playbook.md`.

Submission contract: run(state) -> (orders, conversions, traderData).
"""
from __future__ import annotations

import json
from typing import Any, Dict, List


# Mark roles confirmed from R4 historical data (prosperity-research/03_eda/round4/).
SMART_MARKS_PLUS = {"Mark 14"}     # treat their BUYS as +lean, SELLS as -lean
BAGHOLDER_MARKS_MINUS = {"Mark 38"}  # treat their BUYS as -lean (we go opposite)
BUY_ONLY_VE_PLUS = {"Mark 67"}     # only ever buys VE; small +lean

LEAN_PER_QTY = 0.05      # contribution per traded unit
DECAY_PER_TICK = 0.985   # half-life ~ 46 ticks at 100ts/tick = ~4,600 ts
LEAN_CLAMP = 3.0


def _decode(raw: str) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}


def _encode(state: Dict[str, Any]) -> str:
    blob = json.dumps(state, separators=(",", ":"))
    if len(blob) > 50_000:
        # never cross the truncation boundary
        return blob[:49_900]
    return blob


def update_lean(state_dict: Dict[str, Any], market_trades, current_ts: int) -> None:
    lean: Dict[str, float] = state_dict.setdefault("mark_lean", {})
    last_ts: int = state_dict.get("last_ts", current_ts)

    # decay every product's lean by elapsed ticks
    elapsed_ticks = max(0, (current_ts - last_ts) // 100)
    if elapsed_ticks > 0:
        decay = DECAY_PER_TICK ** elapsed_ticks
        for p in list(lean):
            lean[p] *= decay

    for product, trades in (market_trades or {}).items():
        for t in trades:
            buyer = getattr(t, "buyer", None) or ""
            seller = getattr(t, "seller", None) or ""
            qty = float(getattr(t, "quantity", 0))
            if qty == 0:
                continue
            w = qty * LEAN_PER_QTY
            delta = 0.0
            if buyer in SMART_MARKS_PLUS:
                delta += w
            if seller in SMART_MARKS_PLUS:
                delta -= w
            if buyer in BAGHOLDER_MARKS_MINUS:
                delta -= w
            if seller in BAGHOLDER_MARKS_MINUS:
                delta += w
            if product == "VELVETFRUIT_EXTRACT" and buyer in BUY_ONLY_VE_PLUS:
                delta += 0.5 * w
            if delta != 0.0:
                new_v = lean.get(product, 0.0) + delta
                if new_v > LEAN_CLAMP:
                    new_v = LEAN_CLAMP
                elif new_v < -LEAN_CLAMP:
                    new_v = -LEAN_CLAMP
                lean[product] = new_v

    state_dict["last_ts"] = current_ts


class Trader:
    def run(self, state):  # noqa: D401, ANN001
        td = _decode(state.traderData or "")
        update_lean(td, getattr(state, "market_trades", {}), int(state.timestamp))
        # No orders — observation-only.
        orders: Dict[str, List[object]] = {}
        conversions = 0
        return orders, conversions, _encode(td)
