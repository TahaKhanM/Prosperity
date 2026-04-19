#!/usr/bin/env python3
"""Generate a submission-compatible trader scaffold for a named strategy family."""

from __future__ import annotations

import argparse
from pathlib import Path

from workflow_common import ROOT, ensure_directory, slugify


FAMILIES = {
    "static_fair_value_market_maker": {
        "doc": "prosperity-research/08_playbooks/strategy_templates/static_fair_value_market_maker_strategy_spec.md",
        "summary": "Anchored fair value with inventory-aware passive quoting.",
        "state_keys": ["fair_values", "last_mid"],
        "parameter_block": """{
    "default_spread": 2,
    "inventory_skew_per_unit": 0.02,
    "position_limit": 20,
}""",
        "signal_lines": [
            "fair_value = state_snapshot['fair_values'].get(product, anchor_price(depth))",
            "quote_bid = int(round(fair_value - params['default_spread']))",
            "quote_ask = int(round(fair_value + params['default_spread']))",
        ],
    },
    "moving_fair_value_mean_reversion": {
        "doc": "prosperity-research/08_playbooks/strategy_templates/moving_fair_value_mean_reversion_strategy_spec.md",
        "summary": "Rolling fair value estimate with residual-driven taking and recycling.",
        "state_keys": ["ema_mid", "residual"],
        "parameter_block": """{
    "ema_alpha": 0.2,
    "take_threshold": 2.0,
    "recycle_spread": 1,
    "position_limit": 20,
}""",
        "signal_lines": [
            "fair_value = rolling_fair_value(product, depth, state_snapshot, params)",
            "residual = observed_mid(depth) - fair_value",
            "state_snapshot['residual'][product] = residual",
        ],
    },
    "imbalance_microprice_taker": {
        "doc": "prosperity-research/08_playbooks/strategy_templates/imbalance_microprice_taker_strategy_spec.md",
        "summary": "Short-horizon taker scaffold driven by microprice and depth imbalance.",
        "state_keys": ["last_signal"],
        "parameter_block": """{
    "imbalance_entry": 0.2,
    "imbalance_exit": 0.05,
    "take_clip": 8,
    "position_limit": 20,
}""",
        "signal_lines": [
            "signal = imbalance_signal(depth)",
            "state_snapshot['last_signal'][product] = signal",
            "fair_value = observed_mid(depth) + signal",
        ],
    },
    "inventory_skewed_market_maker": {
        "doc": "prosperity-research/08_playbooks/strategy_templates/inventory_skewed_market_maker_strategy_spec.md",
        "summary": "Passive market maker that skews quotes as inventory and carry risk build.",
        "state_keys": ["inventory_bias"],
        "parameter_block": """{
    "base_spread": 2,
    "skew_per_unit": 0.05,
    "flatten_threshold": 0.85,
    "position_limit": 20,
}""",
        "signal_lines": [
            "fair_value = observed_mid(depth)",
            "inventory_bias = position / max(1, params['position_limit'])",
            "state_snapshot['inventory_bias'][product] = inventory_bias",
        ],
    },
    "event_spike_response": {
        "doc": "prosperity-research/08_playbooks/strategy_templates/event_spike_response_strategy_spec.md",
        "summary": "Sparse event scaffold for spikes, dislocations, and delayed reversion.",
        "state_keys": ["event_state", "last_trigger_ts"],
        "parameter_block": """{
    "spike_threshold": 6.0,
    "cooldown_ticks": 20,
    "reversion_clip": 10,
    "position_limit": 20,
}""",
        "signal_lines": [
            "event_state = detect_spike(product, depth, state_snapshot, params, state.timestamp)",
            "state_snapshot['event_state'][product] = event_state",
            "fair_value = observed_mid(depth)",
        ],
    },
    "hybrid_per_product": {
        "doc": "prosperity-research/08_playbooks/strategy_templates/hybrid_per_product_strategy_spec.md",
        "summary": "Per-product dispatcher so each product family can evolve independently.",
        "state_keys": ["product_modes", "product_state"],
        "parameter_block": """{
    "default_mode": "passive_mm",
    "position_limit": 20,
}""",
        "signal_lines": [
            "mode = state_snapshot['product_modes'].get(product, params['default_mode'])",
            "fair_value = observed_mid(depth)",
            "state_snapshot['product_state'].setdefault(product, {})",
        ],
    },
}

ROUND_DIRS = {
    "tutorial": "Tutorial",
    "round1": "Round1",
    "round2": "Round2",
    "round3": "Round3",
    "round4": "Round4",
    "round5": "Round5",
    "round6": "Round6",
    "round7": "Round7",
    "round8": "Round8",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", choices=sorted(FAMILIES), required=True, help="Strategy family scaffold to generate.")
    parser.add_argument("--round", default="round1", help="Target round folder, for example round1 or round2.")
    parser.add_argument("--name", required=True, help="Trader filename stem to generate.")
    parser.add_argument("--force", action="store_true", help="Overwrite the target file if it already exists.")
    return parser.parse_args()


def normalize_round_dir(round_value: str) -> str:
    key = round_value.strip().lower()
    if key not in ROUND_DIRS:
        raise SystemExit(f"unsupported round '{round_value}'")
    return ROUND_DIRS[key]


def render_template(round_dir: str, family_key: str, trader_name: str) -> str:
    family = FAMILIES[family_key]
    state_dict = ",\n        ".join(f'"{key}": {{}}' for key in family["state_keys"])
    signal_lines = "\n        ".join(family["signal_lines"])
    return f'''import json
from typing import Dict, List, Tuple

from datamodel import Order, OrderDepth, TradingState


ASSUMPTIONS = [
    "Strategy family: {family_key}",
    "Summary: {family['summary']}",
    "Spec doc: {family['doc']}",
    "Edit the parameter block and per-product logic before treating this as a live candidate.",
]

PARAMS = {family["parameter_block"]}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def observed_mid(depth: OrderDepth) -> float:
    bid = max(depth.buy_orders) if depth.buy_orders else None
    ask = min(depth.sell_orders) if depth.sell_orders else None
    if bid is not None and ask is not None:
        return (bid + ask) / 2.0
    if bid is not None:
        return float(bid)
    if ask is not None:
        return float(ask)
    return 0.0


def anchor_price(depth: OrderDepth) -> float:
    return observed_mid(depth)


def imbalance_signal(depth: OrderDepth) -> float:
    best_bid = max(depth.buy_orders) if depth.buy_orders else None
    best_ask = min(depth.sell_orders) if depth.sell_orders else None
    if best_bid is None or best_ask is None:
        return 0.0
    bid_volume = depth.buy_orders[best_bid]
    ask_volume = -depth.sell_orders[best_ask]
    total = bid_volume + ask_volume
    if total <= 0:
        return 0.0
    return (bid_volume - ask_volume) / total


def rolling_fair_value(
    product: str,
    depth: OrderDepth,
    state_snapshot: Dict[str, Dict[str, float]],
    params: Dict[str, float],
) -> float:
    current_mid = observed_mid(depth)
    previous = state_snapshot["ema_mid"].get(product, current_mid)
    alpha = float(params["ema_alpha"])
    fair_value = alpha * current_mid + (1.0 - alpha) * previous
    state_snapshot["ema_mid"][product] = fair_value
    return fair_value


def detect_spike(
    product: str,
    depth: OrderDepth,
    state_snapshot: Dict[str, Dict[str, float]],
    params: Dict[str, float],
    timestamp: int,
) -> str:
    current_mid = observed_mid(depth)
    last_mid = state_snapshot.setdefault("last_mid", {{}}).get(product, current_mid)
    state_snapshot["last_mid"][product] = current_mid
    if abs(current_mid - last_mid) >= float(params["spike_threshold"]):
        state_snapshot["last_trigger_ts"][product] = timestamp
        return "triggered"
    return "idle"


class Trader:
    def __init__(self) -> None:
        self.family = "{family_key}"

    def load_state(self, trader_data: str) -> Dict[str, Dict[str, float]]:
        if trader_data:
            try:
                return json.loads(trader_data)
            except json.JSONDecodeError:
                pass
        return {{
        {state_dict}
        }}

    def save_state(self, state_snapshot: Dict[str, Dict[str, float]]) -> str:
        return json.dumps(state_snapshot, separators=(",", ":"))

    def quote_product(
        self,
        product: str,
        depth: OrderDepth,
        position: int,
        state_snapshot: Dict[str, Dict[str, float]],
    ) -> List[Order]:
        params = PARAMS
        orders: List[Order] = []
        {signal_lines}
        _ = fair_value
        _ = position
        _ = state_snapshot
        # TODO: replace this placeholder with product-specific taking / making logic.
        # Keep one dominant change per iteration and preserve submission compatibility.
        return orders

    def run(self, state: TradingState) -> Tuple[Dict[str, List[Order]], int, str]:
        state_snapshot = self.load_state(state.traderData)
        result: Dict[str, List[Order]] = {{}}
        for product, depth in state.order_depths.items():
            position = state.position.get(product, 0)
            result[product] = self.quote_product(product, depth, position, state_snapshot)
        trader_data = self.save_state(state_snapshot)
        conversions = 0
        return result, conversions, trader_data
'''


def main() -> None:
    args = parse_args()
    round_dir = normalize_round_dir(args.round)
    family_key = args.family
    file_stem = slugify(args.name).replace("-", "_")
    output_dir = ensure_directory(ROOT / "traders" / round_dir / "candidates")
    output_path = output_dir / f"{file_stem}.py"
    if output_path.exists() and not args.force:
        raise SystemExit(f"target already exists: {output_path}")
    output_path.write_text(render_template(round_dir, family_key, file_stem), encoding="utf-8")
    print(f"generated: {output_path.relative_to(ROOT.parent)}")
    print(f"strategy_spec: {FAMILIES[family_key]['doc']}")


if __name__ == "__main__":
    main()
