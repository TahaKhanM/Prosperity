#!/usr/bin/env python3
"""Shared artifact parsing for run diagnostics and comparison reports."""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from workflow_common import read_json, repo_relative


LIMITS = {
    "ASH_COATED_OSMIUM": 80,
    "INTARIAN_PEPPER_ROOT": 80,
}


@dataclass
class SetArtifacts:
    stem: str
    metrics_path: Path
    bundle_path: Path | None
    activity_path: Path | None
    pnl_by_product_path: Path | None
    trades_path: Path | None
    submission_log_path: Path | None
    combined_log_path: Path | None


def _artifact_path(run_dir: Path, stem: str | None, suffix: str) -> Path | None:
    candidates = []
    if stem is None:
        candidates.append(run_dir / suffix)
    else:
        candidates.append(run_dir / f"{stem}-{suffix}")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def find_set_artifacts(run_dir: Path) -> list[SetArtifacts]:
    metrics_files = sorted(run_dir.glob("*-metrics.json"))
    direct_metrics = run_dir / "metrics.json"
    if direct_metrics.is_file():
        metrics_files = [direct_metrics] + metrics_files
    out: list[SetArtifacts] = []
    for metrics_path in metrics_files:
        stem = None if metrics_path.name == "metrics.json" else metrics_path.name[: -len("-metrics.json")]
        out.append(
            SetArtifacts(
                stem=stem or read_json(metrics_path).get("dataset_id", run_dir.name),
                metrics_path=metrics_path,
                bundle_path=_artifact_path(run_dir, stem, "bundle.json"),
                activity_path=_artifact_path(run_dir, stem, "activity.csv"),
                pnl_by_product_path=_artifact_path(run_dir, stem, "pnl_by_product.csv"),
                trades_path=_artifact_path(run_dir, stem, "trades.csv"),
                submission_log_path=_artifact_path(run_dir, stem, "submission.log"),
                combined_log_path=_artifact_path(run_dir, stem, "combined.log"),
            )
        )
    return out


def load_semicolon_csv(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.is_file():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def max_drawdown(values: list[float]) -> float:
    peak = values[0] if values else 0.0
    drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        drawdown = max(drawdown, peak - value)
    return drawdown


def product_book(row: dict[str, Any], product: str) -> tuple[int | None, int | None, float]:
    products = row.get("products") or {}
    book = products.get(product) or {}
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    best_bid = int(bids[0]["price"]) if bids else None
    best_ask = int(asks[0]["price"]) if asks else None
    if best_bid is not None and best_ask is not None:
        mid = float(book.get("mid_price", (best_bid + best_ask) / 2.0))
    elif best_bid is not None:
        mid = float(book.get("mid_price", best_bid))
    elif best_ask is not None:
        mid = float(book.get("mid_price", best_ask))
    else:
        mid = float(book.get("mid_price", 0.0))
    return best_bid, best_ask, mid


def classify_fill(row: dict[str, Any], trade: dict[str, Any]) -> str:
    product = str(trade["symbol"])
    best_bid, best_ask, _ = product_book(row, product)
    price = int(trade["price"])
    if trade.get("buyer") == "SUBMISSION":
        return "aggressive" if best_ask is not None and price >= best_ask else "passive"
    return "aggressive" if best_bid is not None and price <= best_bid else "passive"


def load_run_summary(run_dir: Path) -> dict[str, Any]:
    set_artifacts = find_set_artifacts(run_dir)
    if not set_artifacts:
        raise FileNotFoundError(f"no metrics.json artifacts found under {run_dir}")

    summary: dict[str, Any] = {
        "run_dir": repo_relative(run_dir),
        "set_count": len(set_artifacts),
        "sets": [],
        "products": defaultdict(lambda: {
            "pnl": 0.0,
            "max_long": 0,
            "max_short": 0,
            "max_abs": 0,
            "abs_sum": 0.0,
            "position_points": 0,
            "near_limit_points": 0,
            "final_positions": [],
        }),
        "fills": defaultdict(lambda: {
            "fill_count": 0,
            "quantity": 0,
            "notional": 0.0,
            "edge_h5_sum": 0.0,
            "edge_h5_qty": 0,
            "edge_h20_sum": 0.0,
            "edge_h20_qty": 0,
        }),
        "worst_timestamps": [],
        "total_pnl": 0.0,
        "total_tick_count": 0,
        "total_own_trades": 0,
        "trader_paths": set(),
        "matching_modes": set(),
        "total_drawdown": 0.0,
        "missing_bundle_sets": 0,
    }

    for artifacts in set_artifacts:
        metrics = read_json(artifacts.metrics_path)
        summary["total_pnl"] += float(metrics.get("final_pnl_total", 0.0))
        summary["total_tick_count"] += int(metrics.get("tick_count", 0))
        summary["total_own_trades"] += int(metrics.get("own_trade_count", 0))
        trader_path = metrics.get("trader_path")
        if trader_path:
            summary["trader_paths"].add(str(trader_path))
        matching = metrics.get("matching", {})
        if isinstance(matching, dict) and matching.get("trade_match_mode"):
            summary["matching_modes"].add(str(matching["trade_match_mode"]))

        set_row = {
            "stem": artifacts.stem,
            "dataset_id": metrics.get("dataset_id"),
            "dataset_path": metrics.get("dataset_path"),
            "day": metrics.get("day"),
            "final_pnl_total": float(metrics.get("final_pnl_total", 0.0)),
            "own_trade_count": int(metrics.get("own_trade_count", 0)),
            "tick_count": int(metrics.get("tick_count", 0)),
            "artifacts": {
                "metrics": repo_relative(artifacts.metrics_path),
                "bundle": repo_relative(artifacts.bundle_path) if artifacts.bundle_path else None,
                "activity": repo_relative(artifacts.activity_path) if artifacts.activity_path else None,
                "pnl_by_product": repo_relative(artifacts.pnl_by_product_path) if artifacts.pnl_by_product_path else None,
                "trades": repo_relative(artifacts.trades_path) if artifacts.trades_path else None,
            },
        }
        summary["sets"].append(set_row)

        for product, pnl in (metrics.get("final_pnl_by_product") or {}).items():
            summary["products"][product]["pnl"] += float(pnl)

        pnl_rows = load_semicolon_csv(artifacts.pnl_by_product_path)
        totals = [float(row.get("total", 0.0)) for row in pnl_rows]
        summary["total_drawdown"] = max(summary["total_drawdown"], max_drawdown(totals))
        previous_total = None
        for row in pnl_rows:
            total = float(row.get("total", 0.0))
            if previous_total is None:
                previous_total = total
                continue
            delta_total = total - previous_total
            previous_total = total
            if delta_total >= 0:
                continue
            worst = {
                "set": artifacts.stem,
                "timestamp": int(row.get("timestamp", 0)),
                "delta_total": round(delta_total, 4),
                "total": round(total, 4),
            }
            for column, value in row.items():
                if column in {"timestamp", "total"} or value in {"", None}:
                    continue
                worst[column] = round(float(value), 4)
            summary["worst_timestamps"].append(worst)

        if not artifacts.bundle_path:
            summary["missing_bundle_sets"] += 1
            continue

        bundle = read_json(artifacts.bundle_path)
        rows = bundle.get("timeline") or []
        for product in bundle.get("products") or []:
            positions = [int((row.get("position") or {}).get(product, 0)) for row in rows]
            if positions:
                product_summary = summary["products"][product]
                product_summary["max_long"] = max(product_summary["max_long"], max(positions))
                product_summary["max_short"] = min(product_summary["max_short"], min(positions))
                product_summary["max_abs"] = max(product_summary["max_abs"], max(abs(value) for value in positions))
                product_summary["abs_sum"] += sum(abs(value) for value in positions)
                product_summary["position_points"] += len(positions)
                limit = LIMITS.get(product, 80)
                product_summary["near_limit_points"] += sum(1 for value in positions if abs(value) >= int(limit * 0.9))
                product_summary["final_positions"].append(positions[-1])

        for index, row in enumerate(rows):
            own_trades = row.get("own_trades") or []
            for trade in own_trades:
                product = str(trade["symbol"])
                kind = classify_fill(row, trade)
                side = "buy" if trade.get("buyer") == "SUBMISSION" else "sell"
                key = (product, kind, side)
                fill_summary = summary["fills"][key]
                price = float(trade["price"])
                quantity = int(trade["quantity"])
                fill_summary["fill_count"] += 1
                fill_summary["quantity"] += quantity
                fill_summary["notional"] += price * quantity
                for horizon, edge_key in ((5, "edge_h5_sum"), (20, "edge_h20_sum")):
                    if index + horizon >= len(rows):
                        continue
                    future_mid = product_book(rows[index + horizon], product)[2]
                    signed_edge = (future_mid - price) * (1 if side == "buy" else -1)
                    fill_summary[edge_key] += signed_edge * quantity
                    qty_key = "edge_h5_qty" if horizon == 5 else "edge_h20_qty"
                    fill_summary[qty_key] += quantity

    summary["worst_timestamps"].sort(key=lambda row: row["delta_total"])
    summary["worst_timestamps"] = summary["worst_timestamps"][:25]
    summary["trader_paths"] = sorted(summary["trader_paths"])
    summary["matching_modes"] = sorted(summary["matching_modes"])
    summary["products"] = {product: dict(values) for product, values in summary["products"].items()}
    summary["fills"] = {
        f"{product}|{kind}|{side}": dict(values)
        for (product, kind, side), values in summary["fills"].items()
    }
    return summary


def inventory_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for product, values in sorted(summary["products"].items()):
        points = int(values.get("position_points", 0))
        avg_abs = float(values.get("abs_sum", 0.0)) / points if points else 0.0
        near_limit_fraction = (
            float(values.get("near_limit_points", 0)) / points if points else 0.0
        )
        final_positions = values.get("final_positions") or [0]
        rows.append(
            {
                "product": product,
                "max_long": int(values.get("max_long", 0)),
                "max_short": int(values.get("max_short", 0)),
                "max_abs": int(values.get("max_abs", 0)),
                "avg_abs_position": round(avg_abs, 4),
                "near_limit_fraction": round(near_limit_fraction, 4),
                "final_position_last_set": int(final_positions[-1]),
                "pnl": round(float(values.get("pnl", 0.0)), 4),
            }
        )
    return rows


def fill_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key, values in sorted(summary["fills"].items()):
        product, kind, side = key.split("|")
        quantity = int(values.get("quantity", 0))
        avg_price = float(values.get("notional", 0.0)) / quantity if quantity else 0.0
        edge_h5_qty = int(values.get("edge_h5_qty", 0))
        edge_h20_qty = int(values.get("edge_h20_qty", 0))
        rows.append(
            {
                "product": product,
                "fill_kind": kind,
                "side": side,
                "fill_count": int(values.get("fill_count", 0)),
                "quantity": quantity,
                "avg_price": round(avg_price, 4),
                "edge_h5_avg": round(float(values.get("edge_h5_sum", 0.0)) / edge_h5_qty, 4)
                if edge_h5_qty
                else 0.0,
                "edge_h20_avg": round(float(values.get("edge_h20_sum", 0.0)) / edge_h20_qty, 4)
                if edge_h20_qty
                else 0.0,
            }
        )
    return rows


def headline_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_dir": summary["run_dir"],
        "set_count": summary["set_count"],
        "total_pnl": round(float(summary["total_pnl"]), 4),
        "total_tick_count": int(summary["total_tick_count"]),
        "total_own_trades": int(summary["total_own_trades"]),
        "total_drawdown": round(float(summary["total_drawdown"]), 4),
        "matching_modes": summary["matching_modes"],
        "trader_paths": summary["trader_paths"],
        "products": {
            row["product"]: {
                "pnl": row["pnl"],
                "avg_abs_position": row["avg_abs_position"],
                "near_limit_fraction": row["near_limit_fraction"],
            }
            for row in inventory_rows(summary)
        },
    }


def diagnose_categories(summary: dict[str, Any]) -> list[dict[str, Any]]:
    fills = fill_rows(summary)
    inventory = inventory_rows(summary)
    aggressive_qty = sum(row["quantity"] for row in fills if row["fill_kind"] == "aggressive")
    passive_qty = sum(row["quantity"] for row in fills if row["fill_kind"] == "passive")
    aggressive_edge = (
        sum(row["edge_h5_avg"] * row["quantity"] for row in fills if row["fill_kind"] == "aggressive") / aggressive_qty
        if aggressive_qty
        else 0.0
    )
    passive_edge = (
        sum(row["edge_h5_avg"] * row["quantity"] for row in fills if row["fill_kind"] == "passive") / passive_qty
        if passive_qty
        else 0.0
    )
    combined_qty = aggressive_qty + passive_qty
    combined_edge = (
        (
            sum(row["edge_h5_avg"] * row["quantity"] for row in fills) / combined_qty
        )
        if combined_qty
        else 0.0
    )
    max_near_limit = max((row["near_limit_fraction"] for row in inventory), default=0.0)
    avg_abs_position = max((row["avg_abs_position"] for row in inventory), default=0.0)
    total_drawdown = float(summary["total_drawdown"])
    total_pnl = float(summary["total_pnl"])

    categories = [
        {
            "category": "fair_value",
            "score": max(0.0, -combined_edge * 6.0) + max(0.0, -total_pnl / 10000.0),
            "evidence": (
                f"combined fill edge h5={combined_edge:.3f}, total_pnl={total_pnl:.1f}"
            ),
        },
        {
            "category": "taking_thresholds",
            "score": max(0.0, -aggressive_edge * 8.0) + (aggressive_qty / 200.0 if aggressive_edge < 0 else 0.0),
            "evidence": (
                f"aggressive_qty={aggressive_qty}, aggressive_edge_h5={aggressive_edge:.3f}"
            ),
        },
        {
            "category": "passive_fill_quality",
            "score": max(0.0, -passive_edge * 8.0) + (passive_qty / 200.0 if passive_edge < 0 else 0.0),
            "evidence": (
                f"passive_qty={passive_qty}, passive_edge_h5={passive_edge:.3f}"
            ),
        },
        {
            "category": "inventory_control",
            "score": max_near_limit * 100.0 + avg_abs_position / 10.0 + total_drawdown / 10000.0,
            "evidence": (
                f"max_near_limit={max_near_limit:.3f}, avg_abs_position={avg_abs_position:.1f}, drawdown={total_drawdown:.1f}"
            ),
        },
        {
            "category": "state_path_handling",
            "score": 25.0 if summary["missing_bundle_sets"] else 0.0,
            "evidence": (
                f"missing_bundle_sets={summary['missing_bundle_sets']}, set_count={summary['set_count']}"
            ),
        },
    ]
    categories.sort(key=lambda item: item["score"], reverse=True)
    return categories
