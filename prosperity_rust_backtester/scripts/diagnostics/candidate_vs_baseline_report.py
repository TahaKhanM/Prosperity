#!/usr/bin/env python3
"""Compare two runs on the same dataset and emit a compact report."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

try:
    from common import diagnose_categories, fill_rows, inventory_rows, load_run_summary
except ImportError:  # pragma: no cover - supports package-style imports in smoke tests
    from diagnostics.common import diagnose_categories, fill_rows, inventory_rows, load_run_summary
from workflow_common import RESEARCH_ROOT, ensure_directory, ensure_path, timestamp_slug, write_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", help="Harness run root containing candidate/ and baseline/ child runs.")
    parser.add_argument("--candidate-run", help="Explicit candidate run directory.")
    parser.add_argument("--baseline-run", help="Explicit baseline run directory.")
    parser.add_argument("--report-id", help="Optional report id.")
    return parser.parse_args()


def resolve_run_pair(args: argparse.Namespace) -> tuple[Path, Path]:
    if args.run_root:
        root = ensure_path(args.run_root)
        candidate = root / "candidate"
        baseline = root / "baseline"
        if not candidate.is_dir() or not baseline.is_dir():
            raise SystemExit(f"run root must contain candidate/ and baseline/: {root}")
        return candidate, baseline
    if not args.candidate_run or not args.baseline_run:
        raise SystemExit("pass either --run-root or both --candidate-run and --baseline-run")
    candidate = ensure_path(args.candidate_run)
    baseline = ensure_path(args.baseline_run)
    if not candidate.is_dir() or not baseline.is_dir():
        raise SystemExit("candidate and baseline must both be directories")
    return candidate, baseline


def dataset_signature(summary: dict) -> set[tuple[str | None, str | int | None]]:
    return {(row.get("dataset_id"), row.get("day")) for row in summary["sets"]}


def fill_snapshot(summary: dict) -> dict[str, float]:
    totals = defaultdict(float)
    for row in fill_rows(summary):
        prefix = row["fill_kind"]
        totals[f"{prefix}_quantity"] += float(row["quantity"])
        totals[f"{prefix}_edge_h5_notional"] += float(row["edge_h5_avg"]) * float(row["quantity"])
    for prefix in ("aggressive", "passive"):
        quantity = totals[f"{prefix}_quantity"]
        totals[f"{prefix}_edge_h5_avg"] = (
            totals[f"{prefix}_edge_h5_notional"] / quantity if quantity else 0.0
        )
    return dict(totals)


def inventory_snapshot(summary: dict) -> dict[str, dict[str, float]]:
    return {row["product"]: row for row in inventory_rows(summary)}


def metrics_rows(candidate: dict, baseline: dict) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    def push(metric: str, candidate_value: float | int | str, baseline_value: float | int | str) -> None:
        if isinstance(candidate_value, (int, float)) and isinstance(baseline_value, (int, float)):
            delta = round(float(candidate_value) - float(baseline_value), 4)
        else:
            delta = ""
        rows.append(
            {
                "metric": metric,
                "candidate": candidate_value,
                "baseline": baseline_value,
                "delta": delta,
            }
        )

    push("total_pnl", round(candidate["total_pnl"], 4), round(baseline["total_pnl"], 4))
    push("total_drawdown", round(candidate["total_drawdown"], 4), round(baseline["total_drawdown"], 4))
    push("total_own_trades", candidate["total_own_trades"], baseline["total_own_trades"])
    push("set_count", candidate["set_count"], baseline["set_count"])

    candidate_fills = fill_snapshot(candidate)
    baseline_fills = fill_snapshot(baseline)
    for metric in (
        "aggressive_quantity",
        "aggressive_edge_h5_avg",
        "passive_quantity",
        "passive_edge_h5_avg",
    ):
        push(metric, round(candidate_fills.get(metric, 0.0), 4), round(baseline_fills.get(metric, 0.0), 4))

    candidate_inventory = inventory_snapshot(candidate)
    baseline_inventory = inventory_snapshot(baseline)
    for product in sorted(set(candidate_inventory) | set(baseline_inventory)):
        c_row = candidate_inventory.get(product, {})
        b_row = baseline_inventory.get(product, {})
        push(f"{product}.pnl", round(float(c_row.get("pnl", 0.0)), 4), round(float(b_row.get("pnl", 0.0)), 4))
        push(
            f"{product}.avg_abs_position",
            round(float(c_row.get("avg_abs_position", 0.0)), 4),
            round(float(b_row.get("avg_abs_position", 0.0)), 4),
        )
        push(
            f"{product}.near_limit_fraction",
            round(float(c_row.get("near_limit_fraction", 0.0)), 4),
            round(float(b_row.get("near_limit_fraction", 0.0)), 4),
        )

    return rows


def compare_categories(candidate: dict, baseline: dict) -> list[dict[str, object]]:
    c_scores = {row["category"]: row for row in diagnose_categories(candidate)}
    b_scores = {row["category"]: row for row in diagnose_categories(baseline)}
    rows = []
    for category in (
        "fair_value",
        "taking_thresholds",
        "passive_fill_quality",
        "inventory_control",
        "state_path_handling",
    ):
        c_score = float(c_scores.get(category, {}).get("score", 0.0))
        b_score = float(b_scores.get(category, {}).get("score", 0.0))
        rows.append(
            {
                "category": category,
                "candidate_score": c_score,
                "baseline_score": b_score,
                "delta_score": c_score - b_score,
                "candidate_evidence": c_scores.get(category, {}).get("evidence", ""),
                "baseline_evidence": b_scores.get(category, {}).get("evidence", ""),
            }
        )
    rows.sort(key=lambda row: abs(float(row["delta_score"])), reverse=True)
    return rows


def recommend_next_change(candidate: dict, baseline: dict, category_rows: list[dict[str, object]]) -> tuple[str, str]:
    if category_rows and float(category_rows[0]["delta_score"]) > 0:
        category = str(category_rows[0]["category"])
    else:
        category = diagnose_categories(candidate)[0]["category"]

    mapping = {
        "fair_value": (
            "Retune the fair-value/state estimate before changing aggressiveness.",
            "Both aggressive and passive `edge_h5_avg` should move toward zero or positive values.",
        ),
        "taking_thresholds": (
            "Tighten aggressive taking thresholds before touching passive quoting.",
            "Aggressive `edge_h5_avg` should improve with flat or lower aggressive quantity.",
        ),
        "passive_fill_quality": (
            "Reshade passive quotes by state and inventory rather than widening everything.",
            "Passive `edge_h5_avg` should improve without collapsing passive quantity.",
        ),
        "inventory_control": (
            "Strengthen inventory skew or flattening at the product level.",
            "Near-limit fraction and drawdown should fall before headline PnL is trusted.",
        ),
        "state_path_handling": (
            "Audit state serialization and path handling before any new signal changes.",
            "Per-set dispersion should narrow and missing-bundle/state-confidence issues should disappear.",
        ),
    }
    return mapping[category]


def build_report_md(
    candidate: dict,
    baseline: dict,
    metric_rows: list[dict[str, object]],
    category_rows: list[dict[str, object]],
) -> str:
    recommendation, expected_metric = recommend_next_change(candidate, baseline, category_rows)
    dataset_match = dataset_signature(candidate) == dataset_signature(baseline)
    product_rows = [row for row in metric_rows if row["metric"].endswith(".pnl")]
    headline_rows = [row for row in metric_rows if row["metric"] in {"total_pnl", "total_drawdown", "total_own_trades"}]
    return "\n".join(
        [
            "# Candidate Vs Baseline",
            "",
            "## Inputs",
            "",
            f"- Candidate run: `{candidate['run_dir']}`",
            f"- Baseline run: `{baseline['run_dir']}`",
            f"- Same dataset signature: `{dataset_match}`",
            "",
            "## Headline Deltas",
            "",
            *[
                f"- `{row['metric']}`: candidate `{row['candidate']}` vs baseline `{row['baseline']}` (delta `{row['delta']}`)"
                for row in headline_rows
            ],
            "",
            "## Product Outcome Deltas",
            "",
            *[
                f"- `{row['metric']}` delta `{row['delta']}`"
                for row in product_rows
            ],
            "",
            "## Likely Cause Categories",
            "",
            *[
                (
                    f"- `{row['category']}` delta_score `{float(row['delta_score']):.2f}`. "
                    f"Candidate: {row['candidate_evidence']}. Baseline: {row['baseline_evidence']}."
                )
                for row in category_rows
            ],
            "",
            "## One Next Change",
            "",
            f"- Recommendation: {recommendation}",
            f"- Metric to watch: {expected_metric}",
            "",
            "## Guardrails",
            "",
            "- This report is analysis-only. It does not imply a trader patch by itself.",
            "- If the dataset signature differs, rerun the comparison on matching data before acting on the diagnosis.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    candidate_dir, baseline_dir = resolve_run_pair(args)
    candidate = load_run_summary(candidate_dir)
    baseline = load_run_summary(baseline_dir)

    date_prefix = timestamp_slug()[:8]
    report_date = f"{date_prefix[:4]}-{date_prefix[4:6]}-{date_prefix[6:8]}"
    report_id = args.report_id or f"{report_date}_{candidate_dir.name}_vs_{baseline_dir.name}"
    report_dir = ensure_directory(RESEARCH_ROOT / "06_validation" / "candidate_vs_baseline" / report_id)

    metric_rows = metrics_rows(candidate, baseline)
    category_rows = compare_categories(candidate, baseline)
    write_csv(report_dir / "candidate_vs_baseline_metrics.csv", ["metric", "candidate", "baseline", "delta"], metric_rows)
    (report_dir / "candidate_vs_baseline_report.md").write_text(
        build_report_md(candidate, baseline, metric_rows, category_rows),
        encoding="utf-8",
    )

    print(f"report_dir: {report_dir.relative_to(RESEARCH_ROOT.parent)}")
    print(f"metrics_csv: {(report_dir / 'candidate_vs_baseline_metrics.csv').relative_to(RESEARCH_ROOT.parent)}")
    print(f"report_md: {(report_dir / 'candidate_vs_baseline_report.md').relative_to(RESEARCH_ROOT.parent)}")


if __name__ == "__main__":
    main()
