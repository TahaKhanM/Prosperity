#!/usr/bin/env python3
"""Benchmark a Round 1 trader across the standard robustness matrix."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = ROOT / "runs"
CARGO = ROOT / "scripts" / "cargo_local.sh"
MODES: Tuple[Tuple[str, List[str]], ...] = (
    ("default", []),
    ("worse", ["--trade-match-mode", "worse"]),
    ("queue05", ["--queue-penetration", "0.5"]),
    ("none", ["--trade-match-mode", "none"]),
)
SCORE_WEIGHTS = {
    "default": 1.0,
    "queue05": 0.75,
    "none": 0.5,
}


def bench_run_id(stem: str, mode_name: str) -> str:
    millis = int(time.time() * 1000)
    return f"bench-{stem}-{mode_name}-{millis}"


def run_mode(
    trader: Path,
    dataset: str,
    mode_name: str,
    mode_args: List[str],
    output_root: Path,
) -> Tuple[str, Path]:
    run_id = bench_run_id(trader.stem, mode_name)
    cmd = [
        str(CARGO),
        "run",
        "--",
        "--trader",
        str(trader),
        "--dataset",
        dataset,
        "--run-id",
        run_id,
        "--output-root",
        str(output_root),
        "--artifact-mode",
        "none",
        "--flat",
        "--products",
        "off",
        *mode_args,
    ]
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        raise RuntimeError(f"backtest failed for mode={mode_name}")
    return run_id, output_root / run_id


def load_metrics(run_dir: Path) -> Dict[str, object]:
    totals_by_day: Dict[str, float] = {}
    products_by_day: Dict[str, Dict[str, float]] = {}
    for metrics_path in sorted(run_dir.glob("*-metrics.json")):
        metrics = json.loads(metrics_path.read_text())
        stem = metrics_path.name[: -len("-metrics.json")]
        totals_by_day[stem] = float(metrics["final_pnl_total"])
        products_by_day[stem] = {
            product: float(value)
            for product, value in metrics["final_pnl_by_product"].items()
        }
    total = sum(totals_by_day.values())
    product_totals: Dict[str, float] = {}
    for product_map in products_by_day.values():
        for product, pnl in product_map.items():
            product_totals[product] = product_totals.get(product, 0.0) + pnl
    return {
        "total": total,
        "days": totals_by_day,
        "products": product_totals,
    }


def robust_score(results: Dict[str, Dict[str, object]]) -> float:
    score = 0.0
    for mode_name, weight in SCORE_WEIGHTS.items():
        mode_total = float(results[mode_name]["total"])
        score += weight * mode_total
    return score


def compare_rows(
    current: Dict[str, Dict[str, object]],
    baseline: Dict[str, Dict[str, object]],
) -> Dict[str, object]:
    deltas = {
        mode: float(current[mode]["total"]) - float(baseline[mode]["total"])
        for mode, _ in MODES
    }
    current_score = robust_score(current)
    baseline_score = robust_score(baseline)
    default_days = current["default"]["days"]
    baseline_default_days = baseline["default"]["days"]
    day_deltas = {
        day: float(default_days.get(day, 0.0)) - float(baseline_default_days.get(day, 0.0))
        for day in sorted(set(default_days) | set(baseline_default_days))
    }
    return {
        "score": current_score,
        "baseline_score": baseline_score,
        "score_delta": current_score - baseline_score,
        "total_deltas": deltas,
        "default_day_deltas": day_deltas,
        "non_regression": all(deltas[name] >= 0.0 for name in ("default", "queue05", "none")),
    }


def format_day_table(days: Dict[str, float]) -> str:
    ordered = sorted(days.items())
    return ", ".join(f"{day}={value:.1f}" for day, value in ordered)


def benchmark_trader(trader: Path, dataset: str, output_root: Path) -> Dict[str, Dict[str, object]]:
    results: Dict[str, Dict[str, object]] = {}
    for mode_name, mode_args in MODES:
        run_id, run_dir = run_mode(trader, dataset, mode_name, mode_args, output_root)
        loaded = load_metrics(run_dir)
        loaded["run_id"] = run_id
        loaded["run_dir"] = str(run_dir)
        results[mode_name] = loaded
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trader", required=True)
    parser.add_argument("--compare")
    parser.add_argument("--dataset", default="round1")
    parser.add_argument("--output-root", default=str(RUNS_ROOT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    trader = Path(args.trader)
    if not trader.is_absolute():
        trader = (ROOT / trader).resolve()
    if not trader.exists():
        raise SystemExit(f"missing trader: {trader}")

    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = (ROOT / output_root).resolve()

    current = benchmark_trader(trader, args.dataset, output_root)
    payload: Dict[str, object] = {
        "trader": str(trader),
        "dataset": args.dataset,
        "modes": current,
        "score": robust_score(current),
    }

    baseline = None
    if args.compare:
        baseline_trader = Path(args.compare)
        if not baseline_trader.is_absolute():
            baseline_trader = (ROOT / baseline_trader).resolve()
        if not baseline_trader.exists():
            raise SystemExit(f"missing baseline trader: {baseline_trader}")
        baseline = benchmark_trader(baseline_trader, args.dataset, output_root)
        payload["baseline"] = {
            "trader": str(baseline_trader),
            "modes": baseline,
            "score": robust_score(baseline),
        }
        payload["comparison"] = compare_rows(current, baseline)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print(f"trader: {trader.name}")
    print(f"dataset: {args.dataset}")
    for mode_name, _mode_args in MODES:
        row = current[mode_name]
        print(
            f"{mode_name:>7} total={float(row['total']):9.1f} "
            f"days=[{format_day_table(row['days'])}] "
            f"run_id={row['run_id']}"
        )
    print(f"score={payload['score']:.3f}")

    if baseline is not None:
        comparison = payload["comparison"]
        assert isinstance(comparison, dict)
        print(
            "vs_baseline "
            f"score_delta={float(comparison['score_delta']):.3f} "
            f"default_delta={float(comparison['total_deltas']['default']):.1f} "
            f"queue05_delta={float(comparison['total_deltas']['queue05']):.1f} "
            f"none_delta={float(comparison['total_deltas']['none']):.1f} "
            f"non_regression={comparison['non_regression']}"
        )
        day_deltas = comparison["default_day_deltas"]
        assert isinstance(day_deltas, dict)
        print("default_day_deltas " + ", ".join(f"{day}={delta:.1f}" for day, delta in sorted(day_deltas.items())))


if __name__ == "__main__":
    main()
