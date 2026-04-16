#!/usr/bin/env python3
"""Shared Ash bundle helpers for disagreement and scorecard analysis."""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = ROOT / "runs"
CARGO = ROOT / "scripts" / "cargo_local.sh"

ASH = "ASH_COATED_OSMIUM"
ASH_ANCHOR = 10000.0


@dataclass(frozen=True)
class ModeSpec:
    name: str
    cli_args: Tuple[str, ...]
    trade_match_mode: str
    queue_penetration: float


@dataclass(frozen=True)
class SetArtifacts:
    stem: str
    metrics_path: Path
    bundle_path: Path
    metrics: Dict[str, object]
    bundle: Dict[str, object]


MODE_SPECS: Tuple[ModeSpec, ...] = (
    ModeSpec("default", (), "all", 1.0),
    ModeSpec("worse", ("--trade-match-mode", "worse"), "worse", 1.0),
    ModeSpec("queue05", ("--queue-penetration", "0.5"), "all", 0.5),
    ModeSpec("none", ("--trade-match-mode", "none"), "none", 1.0),
)
MODE_BY_NAME = {spec.name: spec for spec in MODE_SPECS}


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text())


def ensure_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    return path


def bench_run_id(prefix: str, mode_name: str) -> str:
    millis = int(time.time() * 1000)
    return f"{prefix}-{mode_name}-{millis}"


def run_persisted_mode(
    trader: str | Path,
    dataset: str,
    mode: ModeSpec,
    output_root: str | Path,
    run_prefix: str,
) -> Path:
    trader_path = ensure_path(trader)
    output_root_path = ensure_path(output_root)
    run_id = bench_run_id(run_prefix, mode.name)
    cmd = [
        str(CARGO),
        "run",
        "--",
        "--trader",
        str(trader_path),
        "--dataset",
        dataset,
        "--run-id",
        run_id,
        "--output-root",
        str(output_root_path),
        "--persist",
        "--flat",
        "--products",
        "off",
        *mode.cli_args,
    ]
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"persisted backtest failed for {mode.name}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return output_root_path / run_id


def persist_benchmark_matrix(
    trader: str | Path,
    dataset: str,
    output_root: str | Path,
    run_prefix: str,
    modes: Sequence[str] | None = None,
) -> Dict[str, Path]:
    selected = [MODE_BY_NAME[name] for name in (modes or MODE_BY_NAME)]
    run_dirs: Dict[str, Path] = {}
    for mode in selected:
        run_dirs[mode.name] = run_persisted_mode(
            trader=trader,
            dataset=dataset,
            mode=mode,
            output_root=output_root,
            run_prefix=run_prefix,
        )
    return run_dirs


def load_set_artifacts(run_dir: str | Path) -> List[SetArtifacts]:
    run_dir_path = ensure_path(run_dir)
    out: List[SetArtifacts] = []
    for metrics_path in sorted(run_dir_path.glob("*-metrics.json")):
        stem = metrics_path.name[: -len("-metrics.json")]
        bundle_path = run_dir_path / f"{stem}-bundle.json"
        if not bundle_path.exists():
            continue
        out.append(
            SetArtifacts(
                stem=stem,
                metrics_path=metrics_path,
                bundle_path=bundle_path,
                metrics=load_json(metrics_path),
                bundle=load_json(bundle_path),
            )
        )
    return out


def product_book(row: Dict[str, object], product: str) -> Dict[str, object]:
    products = row.get("products") or {}
    book = dict((products.get(product) or {}))  # type: ignore[arg-type]
    bids = list(book.get("bids") or [])
    asks = list(book.get("asks") or [])
    best_bid = int(bids[0]["price"]) if bids else None
    best_ask = int(asks[0]["price"]) if asks else None
    best_bid_volume = int(bids[0]["volume"]) if bids else 0
    best_ask_volume = int(asks[0]["volume"]) if asks else 0
    if best_bid is not None and best_ask is not None:
        mid_price = float(book.get("mid_price", (best_bid + best_ask) / 2.0))
        spread = best_ask - best_bid
    elif best_bid is not None:
        mid_price = float(book.get("mid_price", best_bid))
        spread = None
    elif best_ask is not None:
        mid_price = float(book.get("mid_price", best_ask))
        spread = None
    else:
        mid_price = float(book.get("mid_price", ASH_ANCHOR))
        spread = None
    top_total = best_bid_volume + best_ask_volume
    top_imbalance = (
        (best_bid_volume - best_ask_volume) / top_total if top_total > 0 else 0.0
    )
    if best_bid is not None and best_ask is not None and top_total > 0:
        microprice = (
            best_bid * best_ask_volume + best_ask * best_bid_volume
        ) / top_total
    else:
        microprice = mid_price
    return {
        "bids": bids,
        "asks": asks,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "best_bid_volume": best_bid_volume,
        "best_ask_volume": best_ask_volume,
        "mid_price": mid_price,
        "spread": spread,
        "top_imbalance": top_imbalance,
        "microprice": microprice,
    }


def _cross_depth(levels: Sequence[Dict[str, object]], price: int, side: str) -> int:
    depth = 0
    for idx, level in enumerate(levels, start=1):
        level_price = int(level["price"])
        if side == "buy" and price >= level_price:
            depth = idx
        elif side == "sell" and price <= level_price:
            depth = idx
    return depth


def classify_order_components(
    row: Dict[str, object],
    product: str,
    position_before: int,
) -> Dict[str, object]:
    book = product_book(row, product)
    best_bid = book["best_bid"]
    best_ask = book["best_ask"]
    bids = book["bids"]
    asks = book["asks"]
    ash_orders = [
        order for order in (row.get("orders") or []) if order.get("symbol") == product
    ]
    stats: Dict[str, object] = {
        "order_count": len(ash_orders),
        "aggressive_buy_qty": 0,
        "aggressive_sell_qty": 0,
        "passive_buy_qty": 0,
        "passive_sell_qty": 0,
        "passive_inside_buy_qty": 0,
        "passive_inside_sell_qty": 0,
        "passive_join_buy_qty": 0,
        "passive_join_sell_qty": 0,
        "max_take_depth": 0,
        "aggressive_buy_depth": 0,
        "aggressive_sell_depth": 0,
        "has_passive_buy": False,
        "has_passive_sell": False,
        "has_aggressive_buy": False,
        "has_aggressive_sell": False,
    }
    for order in ash_orders:
        price = int(order["price"])
        quantity = int(order["quantity"])
        if quantity > 0:
            if best_ask is not None and price >= best_ask:
                depth = _cross_depth(asks, price, "buy")
                stats["aggressive_buy_qty"] = int(stats["aggressive_buy_qty"]) + quantity
                stats["aggressive_buy_depth"] = max(int(stats["aggressive_buy_depth"]), depth)
                stats["max_take_depth"] = max(int(stats["max_take_depth"]), depth)
                stats["has_aggressive_buy"] = True
            else:
                stats["passive_buy_qty"] = int(stats["passive_buy_qty"]) + quantity
                stats["has_passive_buy"] = True
                if best_bid is not None and best_ask is not None and best_bid < price < best_ask:
                    stats["passive_inside_buy_qty"] = int(stats["passive_inside_buy_qty"]) + quantity
                else:
                    stats["passive_join_buy_qty"] = int(stats["passive_join_buy_qty"]) + quantity
        elif quantity < 0:
            size = -quantity
            if best_bid is not None and price <= best_bid:
                depth = _cross_depth(bids, price, "sell")
                stats["aggressive_sell_qty"] = int(stats["aggressive_sell_qty"]) + size
                stats["aggressive_sell_depth"] = max(int(stats["aggressive_sell_depth"]), depth)
                stats["max_take_depth"] = max(int(stats["max_take_depth"]), depth)
                stats["has_aggressive_sell"] = True
            else:
                stats["passive_sell_qty"] = int(stats["passive_sell_qty"]) + size
                stats["has_passive_sell"] = True
                if best_bid is not None and best_ask is not None and best_bid < price < best_ask:
                    stats["passive_inside_sell_qty"] = int(stats["passive_inside_sell_qty"]) + size
                else:
                    stats["passive_join_sell_qty"] = int(stats["passive_join_sell_qty"]) + size

    primary_label = "hold"
    actual_family = "hold"
    aggressive_buy_qty = int(stats["aggressive_buy_qty"])
    aggressive_sell_qty = int(stats["aggressive_sell_qty"])
    if aggressive_buy_qty or aggressive_sell_qty:
        if aggressive_buy_qty > aggressive_sell_qty:
            side = "buy"
        elif aggressive_sell_qty > aggressive_buy_qty:
            side = "sell"
        else:
            buy_clear = position_before < 0
            sell_clear = position_before > 0
            if buy_clear and not sell_clear:
                side = "buy"
            elif sell_clear and not buy_clear:
                side = "sell"
            else:
                side = "sell" if aggressive_sell_qty else "buy"
        if side == "buy":
            primary_label = "clear_buy" if position_before < 0 else "take_buy"
        else:
            primary_label = "clear_sell" if position_before > 0 else "take_sell"
        actual_family = "take2" if int(stats["max_take_depth"]) >= 2 else "take1"
    elif bool(stats["has_passive_buy"]) and bool(stats["has_passive_sell"]):
        primary_label = "passive_two_sided"
        actual_family = "mm_inside"
    elif bool(stats["has_passive_buy"]):
        primary_label = "passive_one_sided_buy"
        actual_family = "one_sided_mm"
    elif bool(stats["has_passive_sell"]):
        primary_label = "passive_one_sided_sell"
        actual_family = "one_sided_mm"

    stats["primary_label"] = primary_label
    stats["actual_family"] = actual_family
    stats["aggressive_qty"] = aggressive_buy_qty + aggressive_sell_qty
    return stats


def classify_fill(row: Dict[str, object], trade: Dict[str, object], product: str) -> Optional[str]:
    if trade.get("symbol") != product:
        return None
    book = product_book(row, product)
    best_bid = book["best_bid"]
    best_ask = book["best_ask"]
    price = int(trade["price"])
    if trade.get("buyer") == "SUBMISSION":
        if best_ask is not None and price >= best_ask:
            return "aggressive_buy"
        if best_bid is not None and best_ask is not None and best_bid < price < best_ask:
            return "passive_inside_buy"
        return "passive_buy"
    if trade.get("seller") == "SUBMISSION":
        if best_bid is not None and price <= best_bid:
            return "aggressive_sell"
        if best_bid is not None and best_ask is not None and best_bid < price < best_ask:
            return "passive_inside_sell"
        return "passive_sell"
    return None


def build_product_rows(
    bundle: Dict[str, object],
    product: str = ASH,
) -> List[Dict[str, object]]:
    timeline = list(bundle.get("timeline") or [])
    rows_out: List[Dict[str, object]] = []
    previous_position = 0
    previous_mid: Optional[float] = None
    for row in timeline:
        book = product_book(row, product)
        position_after = int((row.get("position") or {}).get(product, previous_position))
        position_before = previous_position
        mid_price = float(book["mid_price"])
        ret1 = 0.0 if previous_mid is None else mid_price - previous_mid
        micro_gap = float(book["microprice"]) - mid_price
        order_stats = classify_order_components(row, product, position_before)
        fill_counts = {
            "aggressive_buy_fills": 0,
            "aggressive_sell_fills": 0,
            "passive_buy_fills": 0,
            "passive_sell_fills": 0,
            "passive_inside_buy_fills": 0,
            "passive_inside_sell_fills": 0,
            "aggressive_buy_fill_qty": 0,
            "aggressive_sell_fill_qty": 0,
            "passive_buy_fill_qty": 0,
            "passive_sell_fill_qty": 0,
            "passive_inside_buy_fill_qty": 0,
            "passive_inside_sell_fill_qty": 0,
        }
        for trade in row.get("own_trades") or []:
            fill_kind = classify_fill(row, trade, product)
            if fill_kind is None:
                continue
            count_key = f"{fill_kind}_fills"
            qty_key = f"{fill_kind}_fill_qty"
            fill_counts[count_key] = int(fill_counts[count_key]) + 1
            fill_counts[qty_key] = int(fill_counts[qty_key]) + int(trade["quantity"])
        rows_out.append(
            {
                "day": int(row.get("day", 0)),
                "timestamp": int(row.get("timestamp", 0)),
                "position_before": position_before,
                "position_after": position_after,
                "best_bid": book["best_bid"],
                "best_ask": book["best_ask"],
                "spread": book["spread"],
                "mid_price": mid_price,
                "microprice": float(book["microprice"]),
                "top_imbalance": float(book["top_imbalance"]),
                "micro_gap": micro_gap,
                "ret1": ret1,
                "shock": abs(mid_price - ASH_ANCHOR) >= 6.0 or abs(ret1) >= 3.5,
                "anchor_offset": mid_price - ASH_ANCHOR,
                "order_count": int(order_stats["order_count"]),
                "actual_primary_label": str(order_stats["primary_label"]),
                "actual_family": str(order_stats["actual_family"]),
                "aggressive_buy_qty": int(order_stats["aggressive_buy_qty"]),
                "aggressive_sell_qty": int(order_stats["aggressive_sell_qty"]),
                "aggressive_qty": int(order_stats["aggressive_qty"]),
                "passive_buy_qty": int(order_stats["passive_buy_qty"]),
                "passive_sell_qty": int(order_stats["passive_sell_qty"]),
                "passive_inside_buy_qty": int(order_stats["passive_inside_buy_qty"]),
                "passive_inside_sell_qty": int(order_stats["passive_inside_sell_qty"]),
                "passive_join_buy_qty": int(order_stats["passive_join_buy_qty"]),
                "passive_join_sell_qty": int(order_stats["passive_join_sell_qty"]),
                "max_take_depth": int(order_stats["max_take_depth"]),
                **fill_counts,
            }
        )
        previous_position = position_after
        previous_mid = mid_price
    return rows_out


def inventory_summary(rows: Iterable[Dict[str, object]]) -> Dict[str, float]:
    rows_list = list(rows)
    total = len(rows_list)
    if total == 0:
        return {
            "ticks": 0,
            "time_ge_60": 0,
            "time_ge_70": 0,
            "share_ge_60": 0.0,
            "share_ge_70": 0.0,
        }
    time_ge_60 = sum(1 for row in rows_list if abs(int(row["position_after"])) >= 60)
    time_ge_70 = sum(1 for row in rows_list if abs(int(row["position_after"])) >= 70)
    return {
        "ticks": total,
        "time_ge_60": time_ge_60,
        "time_ge_70": time_ge_70,
        "share_ge_60": time_ge_60 / total,
        "share_ge_70": time_ge_70 / total,
    }
