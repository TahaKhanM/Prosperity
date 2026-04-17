#!/usr/bin/env python3
"""Build a medium-spread Ash disagreement dataset against bundle-aligned exact control."""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import round1_exact_control as exact_control
from ash_bundle_utils import (
    ASH,
    MODE_BY_NAME,
    MODE_SPECS,
    ROOT,
    SetArtifacts,
    build_product_rows,
    ensure_path,
    load_set_artifacts,
    persist_benchmark_matrix,
    product_book,
)


LIMIT = exact_control.LIMIT
ACTION_POSITIONS = range(-LIMIT, LIMIT + 1)


def exact_family(action_name: str) -> str:
    if action_name == "hold":
        return "hold"
    if action_name.startswith("mm_"):
        return "mm_inside"
    if "take2" in action_name or "take3" in action_name:
        return "take2"
    if "take1" in action_name:
        return "take1"
    if action_name.startswith(("buy_inside", "sell_inside", "buy_join", "sell_join", "buy_deep", "sell_deep")):
        return "one_sided_mm"
    return "one_sided_mm"


def position_band(position: int) -> str:
    if position >= 60:
        return "long_60_plus"
    if position >= 40:
        return "long_40_59"
    if position >= 20:
        return "long_20_39"
    if position <= -60:
        return "short_60_plus"
    if position <= -40:
        return "short_40_59"
    if position <= -20:
        return "short_20_39"
    return "flat_19"


def richness_bucket(anchor_offset: float) -> str:
    if anchor_offset >= 2.0:
        return "rich"
    if anchor_offset <= -2.0:
        return "cheap"
    return "neutral"


def pressure_bucket(top_imbalance: float, micro_gap: float) -> str:
    if top_imbalance >= 0.34 and micro_gap >= 0.32:
        return "buy_pressure"
    if top_imbalance <= -0.34 and micro_gap <= -0.32:
        return "sell_pressure"
    return "mixed_pressure"


def hosted_class_for_row(row: Dict[str, object]) -> Optional[str]:
    label = str(row["actual_primary_label"])
    if label in {"take_buy", "clear_buy"}:
        return "take_a1"
    if label in {"take_sell", "clear_sell"}:
        return "take_b1"
    if label == "passive_one_sided_buy":
        return "passive_inside_buy"
    if label == "passive_one_sided_sell":
        return "passive_inside_sell"
    return None


def bundle_ticks(bundle: Dict[str, object], product: str = ASH) -> List[exact_control.Tick]:
    out: List[exact_control.Tick] = []
    for row in bundle.get("timeline") or []:
        book = product_book(row, product)
        bids = tuple(
            (int(level["price"]), int(level["volume"])) for level in (book["bids"] or [])
        )
        asks = tuple(
            (int(level["price"]), int(level["volume"])) for level in (book["asks"] or [])
        )
        market_trades = tuple(
            exact_control.MarketTrade(
                price=int(trade["price"]),
                quantity=int(trade["quantity"]),
            )
            for trade in (row.get("market_trades") or [])
            if trade.get("symbol") == product
        )
        out.append(
            exact_control.Tick(
                timestamp=int(row.get("timestamp", 0)),
                bids=bids,
                asks=asks,
                market_trades=market_trades,
                mark=float(book["mid_price"]),
            )
        )
    return out


def solve_exact_rows(
    artifacts: SetArtifacts,
    mode_name: str,
) -> List[Dict[str, object]]:
    mode = MODE_BY_NAME[mode_name]
    actual_rows = build_product_rows(artifacts.bundle, ASH)
    ticks = bundle_ticks(artifacts.bundle, ASH)
    if not ticks:
        return []
    positions_before = [int(row["position_before"]) for row in actual_rows]
    summaries: List[Dict[str, object]] = [{} for _ in ticks]
    terminal_mark = ticks[-1].mark
    value_next = {pos: pos * terminal_mark for pos in ACTION_POSITIONS}
    for tick_idx in range(len(ticks) - 1, -1, -1):
        tick = ticks[tick_idx]
        target_position = positions_before[tick_idx]
        current_values: Dict[int, float] = {}
        target_summary: Optional[Dict[str, object]] = None
        for position in ACTION_POSITIONS:
            best_action = "hold"
            best_value = float("-inf")
            runner_action = "hold"
            runner_value = float("-inf")
            family_values: Dict[str, float] = {}
            for action in exact_control.candidate_actions(ASH, position):
                legs = exact_control.materialize_action(tick, action)
                if legs is None:
                    continue
                try:
                    new_position, cash_delta = exact_control.simulate_action(
                        tick,
                        position,
                        legs,
                        trade_match_mode=mode.trade_match_mode,
                        queue_penetration=mode.queue_penetration,
                    )
                except ValueError:
                    continue
                value = cash_delta + value_next[new_position]
                family = exact_family(action.name)
                if value > family_values.get(family, float("-inf")):
                    family_values[family] = value
                if value > best_value:
                    runner_action, runner_value = best_action, best_value
                    best_action, best_value = action.name, value
                elif value > runner_value:
                    runner_action, runner_value = action.name, value
            current_values[position] = best_value
            if position == target_position:
                target_summary = {
                    "exact_best_action": best_action,
                    "exact_best_family": exact_family(best_action),
                    "exact_value": best_value,
                    "best_runner_up": runner_action if math.isfinite(runner_value) else best_action,
                    "runner_up_value": runner_value if math.isfinite(runner_value) else best_value,
                    "family_values": family_values,
                }
        value_next = current_values
        summaries[tick_idx] = target_summary or {
            "exact_best_action": "hold",
            "exact_best_family": "hold",
            "exact_value": value_next.get(target_position, 0.0),
            "best_runner_up": "hold",
            "runner_up_value": value_next.get(target_position, 0.0),
            "family_values": {"hold": value_next.get(target_position, 0.0)},
        }
    return summaries


def write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    if not rows:
        path.write_text("")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_official_export(official_bundle: Path, trader: Path, export_dir: Path) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "analyze_official_logs.py"),
        str(official_bundle),
        "--replay-trader",
        str(trader),
        "--export-dir",
        str(export_dir),
    ]
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "official log export failed\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )


def load_hosted_metrics(export_dir: Path) -> Dict[Tuple[str, int], Dict[str, object]]:
    metrics: Dict[Tuple[str, int], Dict[str, object]] = {}
    events_paths = sorted(export_dir.glob("*_submission_trade_events.csv"))
    if not events_paths:
        return metrics
    rollup: Dict[Tuple[str, int], Dict[str, float]] = defaultdict(lambda: {"count": 0.0, "qty": 0.0, "markout_h10": 0.0})
    for path in events_paths:
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if row.get("product") != ASH:
                    continue
                trade_class = str(row.get("trade_class") or "")
                spread = int(float(row.get("spread_0") or 0))
                quantity = int(float(row.get("quantity") or 0))
                markout = row.get("markout_h10")
                key = (trade_class, spread)
                rollup[key]["count"] += 1.0
                rollup[key]["qty"] += quantity
                if markout not in ("", None):
                    rollup[key]["markout_h10"] += float(markout)
    for key, item in rollup.items():
        count = int(item["count"])
        metrics[key] = {
            "hosted_count": count,
            "hosted_qty": int(item["qty"]),
            "hosted_markout_h10_avg": (item["markout_h10"] / count) if count else None,
        }
    return metrics


def donor_bucket_rows(
    rows: Iterable[Dict[str, object]],
    hosted_metrics: Dict[Tuple[str, int], Dict[str, object]],
    *,
    include_mode: bool,
) -> List[Dict[str, object]]:
    rollup: Dict[Tuple[object, ...], Dict[str, object]] = {}
    for row in rows:
        if float(row["recoverable_value"]) <= 0.0:
            continue
        if str(row["actual_family"]) == str(row["exact_best_family"]):
            continue
        if include_mode:
            key = (
                row["mode"],
                row["actual_primary_label"],
                row["exact_best_family"],
                row["spread"],
                row["position_band"],
                row["richness_bucket"],
                row["pressure_bucket"],
                row["shock_bucket"],
            )
        else:
            key = (
                row["actual_primary_label"],
                row["exact_best_family"],
                row["spread"],
                row["position_band"],
                row["richness_bucket"],
                row["pressure_bucket"],
                row["shock_bucket"],
            )
        hosted_class = row.get("hosted_ref_class")
        hosted_spread = int(row["spread"])
        hosted = hosted_metrics.get((str(hosted_class), hosted_spread), {})
        bucket = rollup.setdefault(
            key,
            {
                "count": 0,
                "recoverable_total": 0.0,
                "recoverable_max": 0.0,
                "actual_action": row["actual_primary_label"],
                "exact_best_family": row["exact_best_family"],
                "spread": row["spread"],
                "position_band": row["position_band"],
                "richness_bucket": row["richness_bucket"],
                "pressure_bucket": row["pressure_bucket"],
                "shock_bucket": row["shock_bucket"],
                "hosted_ref_class": hosted_class,
                "hosted_count": hosted.get("hosted_count"),
                "hosted_qty": hosted.get("hosted_qty"),
                "hosted_markout_h10_avg": hosted.get("hosted_markout_h10_avg"),
                "hosted_veto": False,
            },
        )
        if include_mode:
            bucket["mode"] = row["mode"]
        bucket["count"] = int(bucket["count"]) + 1
        bucket["recoverable_total"] = float(bucket["recoverable_total"]) + float(row["recoverable_value"])
        bucket["recoverable_max"] = max(float(bucket["recoverable_max"]), float(row["recoverable_value"]))
    out: List[Dict[str, object]] = []
    for bucket in rollup.values():
        count = int(bucket["count"])
        hosted_markout = bucket.get("hosted_markout_h10_avg")
        actual_action = str(bucket["actual_action"])
        exact_best_family = str(bucket["exact_best_family"])
        suppressive = actual_action.startswith(("take_", "clear_")) and exact_best_family in {"hold", "one_sided_mm", "mm_inside"}
        if suppressive and isinstance(hosted_markout, (int, float)) and hosted_markout > 0.0:
            bucket["hosted_veto"] = True
        bucket["recoverable_avg"] = float(bucket["recoverable_total"]) / count if count else 0.0
        out.append(bucket)
    out.sort(
        key=lambda row: (
            bool(row.get("hosted_veto")),
            -float(row["recoverable_total"]),
            -float(row["recoverable_avg"]),
            -int(row["count"]),
        )
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-trader", required=True)
    parser.add_argument("--dataset", default="round1")
    parser.add_argument("--official-bundle", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    baseline_trader = ensure_path(args.baseline_trader)
    official_bundle = ensure_path(args.official_bundle)
    output_dir = ensure_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline_root = output_dir / "baseline"
    baseline_root.mkdir(parents=True, exist_ok=True)
    run_dirs = persist_benchmark_matrix(
        trader=baseline_trader,
        dataset=args.dataset,
        output_root=baseline_root,
        run_prefix=f"{output_dir.name}-ash-baseline",
        modes=[spec.name for spec in MODE_SPECS],
    )

    official_export_dir = output_dir / "official"
    run_official_export(official_bundle, baseline_trader, official_export_dir)
    hosted_metrics = load_hosted_metrics(official_export_dir)

    disagreement_rows: List[Dict[str, object]] = []
    mode_summaries: List[Dict[str, object]] = []
    for mode_name, run_dir in run_dirs.items():
        artifacts_list = load_set_artifacts(run_dir)
        ash_total = 0.0
        for artifacts in artifacts_list:
            exact_rows = solve_exact_rows(artifacts, mode_name)
            actual_rows = build_product_rows(artifacts.bundle, ASH)
            ash_total += float(artifacts.metrics.get("final_pnl_by_product", {}).get(ASH, 0.0))
            for actual, exact_row in zip(actual_rows, exact_rows):
                spread = actual["spread"]
                if spread is None or not (9 <= int(spread) <= 13):
                    continue
                actual_family_value = exact_row["family_values"].get(str(actual["actual_family"]))
                recoverable_value = None
                if isinstance(actual_family_value, (int, float)):
                    recoverable_value = float(exact_row["exact_value"]) - float(actual_family_value)
                hosted_ref_class = hosted_class_for_row(actual)
                hosted = hosted_metrics.get((str(hosted_ref_class), int(spread)), {})
                disagreement_rows.append(
                    {
                        "mode": mode_name,
                        "set": artifacts.stem,
                        "day": int(actual["day"]),
                        "timestamp": int(actual["timestamp"]),
                        "position_before": int(actual["position_before"]),
                        "position_after": int(actual["position_after"]),
                        "position_band": position_band(int(actual["position_before"])),
                        "best_bid": actual["best_bid"],
                        "best_ask": actual["best_ask"],
                        "spread": int(spread),
                        "mid_price": float(actual["mid_price"]),
                        "microprice": float(actual["microprice"]),
                        "anchor_offset": float(actual["anchor_offset"]),
                        "richness_bucket": richness_bucket(float(actual["anchor_offset"])),
                        "top_imbalance": float(actual["top_imbalance"]),
                        "micro_gap": float(actual["micro_gap"]),
                        "pressure_bucket": pressure_bucket(float(actual["top_imbalance"]), float(actual["micro_gap"])),
                        "ret1": float(actual["ret1"]),
                        "shock": bool(actual["shock"]),
                        "shock_bucket": "shock" if bool(actual["shock"]) else "steady",
                        "order_count": int(actual["order_count"]),
                        "actual_primary_label": str(actual["actual_primary_label"]),
                        "actual_family": str(actual["actual_family"]),
                        "aggressive_buy_qty": int(actual["aggressive_buy_qty"]),
                        "aggressive_sell_qty": int(actual["aggressive_sell_qty"]),
                        "aggressive_qty": int(actual["aggressive_qty"]),
                        "passive_buy_qty": int(actual["passive_buy_qty"]),
                        "passive_sell_qty": int(actual["passive_sell_qty"]),
                        "passive_inside_buy_qty": int(actual["passive_inside_buy_qty"]),
                        "passive_inside_sell_qty": int(actual["passive_inside_sell_qty"]),
                        "max_take_depth": int(actual["max_take_depth"]),
                        "exact_best_action": str(exact_row["exact_best_action"]),
                        "exact_best_family": str(exact_row["exact_best_family"]),
                        "exact_value": round(float(exact_row["exact_value"]), 6),
                        "best_runner_up": str(exact_row["best_runner_up"]),
                        "ev_gap": round(float(exact_row["exact_value"]) - float(exact_row["runner_up_value"]), 6),
                        "actual_family_value": None if actual_family_value is None else round(float(actual_family_value), 6),
                        "recoverable_value": None if recoverable_value is None else round(recoverable_value, 6),
                        "hosted_ref_class": hosted_ref_class,
                        "hosted_count": hosted.get("hosted_count"),
                        "hosted_qty": hosted.get("hosted_qty"),
                        "hosted_markout_h10_avg": hosted.get("hosted_markout_h10_avg"),
                    }
                )
        mode_summaries.append(
            {
                "mode": mode_name,
                "run_dir": str(run_dir),
                "ash_total": ash_total,
            }
        )

    disagreement_rows.sort(
        key=lambda row: (
            row["mode"],
            row["set"],
            int(row["timestamp"]),
        )
    )
    donor_rows = donor_bucket_rows(disagreement_rows, hosted_metrics, include_mode=True)
    conservative_rows = donor_bucket_rows(
        [row for row in disagreement_rows if row["mode"] in {"worse", "queue05", "none"}],
        hosted_metrics,
        include_mode=False,
    )

    write_csv(output_dir / "medium_spread_disagreement.csv", disagreement_rows)
    write_csv(output_dir / "donor_buckets.csv", donor_rows)
    write_csv(output_dir / "donor_buckets_conservative.csv", conservative_rows)
    summary = {
        "baseline_trader": str(baseline_trader),
        "official_bundle": str(official_bundle),
        "baseline_runs": {mode: str(path) for mode, path in run_dirs.items()},
        "mode_summaries": mode_summaries,
        "row_count": len(disagreement_rows),
        "top_donors": conservative_rows[:15],
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    print(f"baseline_trader={baseline_trader}")
    for row in mode_summaries:
        print(f"{row['mode']}: ash_total={row['ash_total']:.1f} run_dir={row['run_dir']}")
    print(f"medium_spread_rows={len(disagreement_rows)}")
    print("top conservative donor buckets:")
    for row in conservative_rows[:12]:
        print(
            f"  actual={row['actual_action']} best={row['exact_best_family']}"
            f" spread={row['spread']} pos={row['position_band']}"
            f" pressure={row['pressure_bucket']} rich={row['richness_bucket']}"
            f" recoverable={row['recoverable_total']:.1f}"
            f" count={row['count']}"
            f" hosted_veto={row['hosted_veto']}"
        )


if __name__ == "__main__":
    main()
