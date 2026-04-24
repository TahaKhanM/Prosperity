#!/usr/bin/env python3
"""Compare persisted Ash run bundles across the four validation modes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from ash_bundle_utils import (
    ASH,
    MODE_BY_NAME,
    build_product_rows,
    ensure_path,
    inventory_summary,
    load_set_artifacts,
)


def parse_mode_paths(items: Iterable[str]) -> Dict[str, Path]:
    out: Dict[str, Path] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"expected mode=run_dir, got: {item}")
        mode_name, raw_path = item.split("=", 1)
        mode_name = mode_name.strip()
        if mode_name not in MODE_BY_NAME:
            raise SystemExit(f"unknown mode: {mode_name}")
        out[mode_name] = ensure_path(raw_path.strip())
    return out


def mode_metrics(run_dir: Path) -> Dict[str, object]:
    set_metrics: List[Dict[str, object]] = []
    ash_total = 0.0
    own_trades_total = 0
    all_rows: List[Dict[str, object]] = []
    long_rich_counts = {20: 0, 40: 0, 60: 0}
    final_positions: Dict[str, int] = {}
    for artifacts in load_set_artifacts(run_dir):
        rows = build_product_rows(artifacts.bundle, ASH)
        all_rows.extend(rows)
        ash_pnl = float(artifacts.metrics.get("final_pnl_by_product", {}).get(ASH, 0.0))
        own_trades = int(artifacts.metrics.get("own_trade_count", 0))
        ash_total += ash_pnl
        own_trades_total += own_trades
        final_position = int(rows[-1]["position_after"]) if rows else 0
        final_positions[artifacts.stem] = final_position
        set_metrics.append(
            {
                "set": artifacts.stem,
                "ash_pnl": ash_pnl,
                "own_trades": own_trades,
                "final_position": final_position,
            }
        )
        for row in rows:
            if int(row["spread"] or 0) < 10 or int(row["spread"] or 0) > 13:
                continue
            if str(row["actual_primary_label"]) not in {"take_sell", "clear_sell"}:
                continue
            if float(row["anchor_offset"]) < 2.0:
                continue
            for threshold in long_rich_counts:
                if int(row["position_before"]) >= threshold:
                    long_rich_counts[threshold] += 1

    aggressive_rows = [
        row
        for row in all_rows
        if 9 <= int(row["spread"] or 0) <= 13 and str(row["actual_primary_label"]).startswith(("take_", "clear_"))
    ]
    inventory = inventory_summary(all_rows)
    aggressive_fill_qty = sum(
        int(row["aggressive_buy_fill_qty"]) + int(row["aggressive_sell_fill_qty"])
        for row in all_rows
    )
    passive_inside_fill_qty = sum(
        int(row["passive_inside_buy_fill_qty"]) + int(row["passive_inside_sell_fill_qty"])
        for row in all_rows
    )
    ash_fill_count = sum(
        int(row["aggressive_buy_fills"])
        + int(row["aggressive_sell_fills"])
        + int(row["passive_buy_fills"])
        + int(row["passive_sell_fills"])
        + int(row["passive_inside_buy_fills"])
        + int(row["passive_inside_sell_fills"])
        for row in all_rows
    )
    return {
        "run_dir": str(run_dir),
        "ash_total": ash_total,
        "own_trades_total": own_trades_total,
        "ash_fill_count": ash_fill_count,
        "aggressive_action_count_9_13": len(aggressive_rows),
        "aggressive_action_qty_9_13": sum(int(row["aggressive_qty"]) for row in aggressive_rows),
        "long_rich_sell_take_clear_counts": long_rich_counts,
        "inventory": inventory,
        "passive_inside_fill_qty": passive_inside_fill_qty,
        "aggressive_fill_qty": aggressive_fill_qty,
        "final_positions": final_positions,
        "sets": set_metrics,
    }


def compare_mode(candidate: Dict[str, object], baseline: Dict[str, object]) -> Dict[str, object]:
    inventory_candidate = candidate["inventory"]
    inventory_baseline = baseline["inventory"]
    final_position_delta = {
        set_name: int(candidate["final_positions"].get(set_name, 0)) - int(baseline["final_positions"].get(set_name, 0))
        for set_name in sorted(set(candidate["final_positions"]) | set(baseline["final_positions"]))
    }
    return {
        "ash_delta": float(candidate["ash_total"]) - float(baseline["ash_total"]),
        "own_trades_delta": int(candidate["own_trades_total"]) - int(baseline["own_trades_total"]),
        "ash_fill_count_delta": int(candidate["ash_fill_count"]) - int(baseline["ash_fill_count"]),
        "aggressive_action_count_9_13_delta": int(candidate["aggressive_action_count_9_13"]) - int(baseline["aggressive_action_count_9_13"]),
        "aggressive_action_qty_9_13_delta": int(candidate["aggressive_action_qty_9_13"]) - int(baseline["aggressive_action_qty_9_13"]),
        "long_rich_sell_take_clear_delta": {
            key: int(candidate["long_rich_sell_take_clear_counts"][key]) - int(baseline["long_rich_sell_take_clear_counts"][key])
            for key in (20, 40, 60)
        },
        "inventory_delta": {
            "time_ge_60": int(inventory_candidate["time_ge_60"]) - int(inventory_baseline["time_ge_60"]),
            "time_ge_70": int(inventory_candidate["time_ge_70"]) - int(inventory_baseline["time_ge_70"]),
            "share_ge_60": float(inventory_candidate["share_ge_60"]) - float(inventory_baseline["share_ge_60"]),
            "share_ge_70": float(inventory_candidate["share_ge_70"]) - float(inventory_baseline["share_ge_70"]),
        },
        "passive_inside_fill_qty_delta": int(candidate["passive_inside_fill_qty"]) - int(baseline["passive_inside_fill_qty"]),
        "aggressive_fill_qty_delta": int(candidate["aggressive_fill_qty"]) - int(baseline["aggressive_fill_qty"]),
        "final_position_delta": final_position_delta,
    }


def promotion_summary(comparison: Dict[str, Dict[str, object]], baseline: Dict[str, Dict[str, object]], candidate: Dict[str, Dict[str, object]]) -> Dict[str, object]:
    queue05_delta = float(comparison["queue05"]["ash_delta"])
    none_delta = float(comparison["none"]["ash_delta"])
    worse_delta = float(comparison["worse"]["ash_delta"])
    default_delta = float(comparison["default"]["ash_delta"])
    conservative_gain = worse_delta + queue05_delta + none_delta
    own_trade_ratio_ok = True
    for mode_name in MODE_BY_NAME:
        base_own = int(baseline[mode_name]["own_trades_total"])
        cand_own = int(candidate[mode_name]["own_trades_total"])
        if base_own > 0 and cand_own > base_own * 1.05:
            own_trade_ratio_ok = False
            break
    inventory_ok = False
    for mode_name in ("queue05", "none"):
        base_share = float(baseline[mode_name]["inventory"]["share_ge_60"])
        cand_share = float(candidate[mode_name]["inventory"]["share_ge_60"])
        if cand_share <= base_share - 0.03:
            inventory_ok = True
        if base_share > 0.0 and cand_share <= base_share * 0.9:
            inventory_ok = True
    long_rich_ok = any(
        int(comparison[mode_name]["long_rich_sell_take_clear_delta"][60]) < 0
        or int(comparison[mode_name]["long_rich_sell_take_clear_delta"][40]) < 0
        for mode_name in ("worse", "queue05", "none")
    )
    passive_inside_delta_total = sum(int(comparison[mode]["passive_inside_fill_qty_delta"]) for mode in MODE_BY_NAME)
    aggressive_fill_delta_total = sum(int(comparison[mode]["aggressive_fill_qty_delta"]) for mode in MODE_BY_NAME)
    passive_farming_risk = conservative_gain > 0.0 and passive_inside_delta_total > max(25, 2 * max(0, aggressive_fill_delta_total))

    reasons: List[str] = []
    if queue05_delta < 150.0:
        reasons.append("queue05 gain below +150")
    if none_delta < 150.0:
        reasons.append("none gain below +150")
    if conservative_gain < 600.0:
        reasons.append("worse+queue05+none gain below +600")
    if default_delta < -50.0:
        reasons.append("default regressed by more than -50")
    if worse_delta < -50.0:
        reasons.append("worse regressed by more than -50")
    if not own_trade_ratio_ok:
        reasons.append("own trade count rose by more than 5% in at least one mode")
    if not inventory_ok:
        reasons.append("|pos| >= 60 occupancy did not improve enough in queue05 or none")
    if not long_rich_ok:
        reasons.append("long-rich sell-side take/clear counts did not decline in conservative modes")
    if passive_farming_risk:
        reasons.append("gains appear too dependent on extra passive-inside fills")

    return {
        "queue05_delta": queue05_delta,
        "none_delta": none_delta,
        "worse_delta": worse_delta,
        "default_delta": default_delta,
        "conservative_gain": conservative_gain,
        "passive_inside_fill_qty_delta_total": passive_inside_delta_total,
        "aggressive_fill_qty_delta_total": aggressive_fill_delta_total,
        "promote": not reasons,
        "reject_reasons": reasons,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="append", required=True, help="mode=/abs/path/to/run_dir")
    parser.add_argument("--candidate", action="append", required=True, help="mode=/abs/path/to/run_dir")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    baseline_paths = parse_mode_paths(args.baseline)
    candidate_paths = parse_mode_paths(args.candidate)
    missing_baseline = sorted(set(MODE_BY_NAME) - set(baseline_paths))
    missing_candidate = sorted(set(MODE_BY_NAME) - set(candidate_paths))
    if missing_baseline or missing_candidate:
        raise SystemExit(
            f"missing modes baseline={missing_baseline} candidate={missing_candidate}"
        )

    baseline_metrics = {mode: mode_metrics(path) for mode, path in baseline_paths.items()}
    candidate_metrics = {mode: mode_metrics(path) for mode, path in candidate_paths.items()}
    comparison = {
        mode: compare_mode(candidate_metrics[mode], baseline_metrics[mode])
        for mode in MODE_BY_NAME
    }
    promotion = promotion_summary(comparison, baseline_metrics, candidate_metrics)
    payload = {
        "baseline": baseline_metrics,
        "candidate": candidate_metrics,
        "comparison": comparison,
        "promotion": promotion,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    for mode in MODE_BY_NAME:
        row = comparison[mode]
        print(
            f"{mode}: ash_delta={row['ash_delta']:.1f}"
            f" own_trades_delta={row['own_trades_delta']}"
            f" aggr_rows_9_13_delta={row['aggressive_action_count_9_13_delta']}"
            f" inv60_delta={row['inventory_delta']['time_ge_60']}"
            f" inv70_delta={row['inventory_delta']['time_ge_70']}"
            f" passive_inside_fill_qty_delta={row['passive_inside_fill_qty_delta']}"
            f" aggressive_fill_qty_delta={row['aggressive_fill_qty_delta']}"
        )
        print(
            f"  long_rich_sell_take_clear_delta"
            f" pos20={row['long_rich_sell_take_clear_delta'][20]}"
            f" pos40={row['long_rich_sell_take_clear_delta'][40]}"
            f" pos60={row['long_rich_sell_take_clear_delta'][60]}"
        )
        print(f"  final_position_delta={row['final_position_delta']}")
    print(
        f"promotion promote={promotion['promote']}"
        f" conservative_gain={promotion['conservative_gain']:.1f}"
        f" reject_reasons={promotion['reject_reasons']}"
    )


if __name__ == "__main__":
    main()
