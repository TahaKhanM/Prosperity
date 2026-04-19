#!/usr/bin/env python3
"""Turn a backtest run into a compact diagnosis packet."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from common import diagnose_categories, fill_rows, headline_metrics, inventory_rows, load_run_summary
except ImportError:  # pragma: no cover - supports package-style imports in smoke tests
    from diagnostics.common import (
        diagnose_categories,
        fill_rows,
        headline_metrics,
        inventory_rows,
        load_run_summary,
    )
from workflow_common import RESEARCH_ROOT, ensure_directory, ensure_path, timestamp_slug, write_csv, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        required=True,
        help="Run directory or run root created by scripts/run_harness.py.",
    )
    parser.add_argument(
        "--set",
        choices=("candidate", "baseline"),
        default="candidate",
        help="Which child run to inspect when --run points at a harness run root.",
    )
    parser.add_argument(
        "--packet-id",
        help="Optional packet id. Defaults to <YYYY-MM-DD>_<run-stem>.",
    )
    return parser.parse_args()


def resolve_run_dir(run_value: str, set_name: str) -> Path:
    candidate = ensure_path(run_value)
    if (candidate / "run_manifest.json").is_file():
        child = candidate / set_name
        if child.is_dir():
            return child
        raise SystemExit(f"run root has no '{set_name}' child: {candidate}")
    if candidate.is_dir():
        return candidate
    raise SystemExit(f"missing run directory: {candidate}")


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    header = "| " + " | ".join(headers) + " |"
    divider = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header, divider, *body])


def build_run_summary_md(summary: dict, categories: list[dict]) -> str:
    inventory = inventory_rows(summary)
    top_categories = categories[:3]
    inventory_table = markdown_table(
        ["Product", "PnL", "Avg |pos|", "Near limit", "Max |pos|"],
        [
            [
                row["product"],
                f"{row['pnl']:.1f}",
                f"{row['avg_abs_position']:.2f}",
                f"{row['near_limit_fraction']:.2%}",
                str(row["max_abs"]),
            ]
            for row in inventory
        ]
        or [["n/a", "0.0", "0.00", "0.00%", "0"]],
    )
    category_lines = "\n".join(
        f"- `{item['category']}` score={item['score']:.2f} from {item['evidence']}" for item in top_categories
    )
    return "\n".join(
        [
            f"# Run Summary: {summary['run_dir']}",
            "",
            "## Headline",
            "",
            f"- Total PnL: `{summary['total_pnl']:.2f}`",
            f"- Drawdown: `{summary['total_drawdown']:.2f}`",
            f"- Own trades: `{summary['total_own_trades']}`",
            f"- Set count: `{summary['set_count']}`",
            f"- Matching modes: `{', '.join(summary['matching_modes']) or 'unknown'}`",
            "",
            "## Product Inventory And PnL",
            "",
            inventory_table,
            "",
            "## Primary Risk Categories",
            "",
            category_lines or "- No diagnosis categories available.",
            "",
        ]
    )


def build_diagnosis_packet_md(summary: dict, categories: list[dict]) -> str:
    worst_rows = summary["worst_timestamps"][:5]
    fill_summary = fill_rows(summary)
    passive_rows = [row for row in fill_summary if row["fill_kind"] == "passive"]
    aggressive_rows = [row for row in fill_summary if row["fill_kind"] == "aggressive"]
    passive_edge = sum(row["edge_h5_avg"] * row["quantity"] for row in passive_rows)
    passive_qty = sum(row["quantity"] for row in passive_rows)
    aggressive_edge = sum(row["edge_h5_avg"] * row["quantity"] for row in aggressive_rows)
    aggressive_qty = sum(row["quantity"] for row in aggressive_rows)
    likely_failure = categories[0]["category"] if categories else "unknown"

    worst_table = markdown_table(
        ["Set", "Timestamp", "Delta total", "Total"],
        [
            [
                str(row["set"]),
                str(row["timestamp"]),
                f"{row['delta_total']:.2f}",
                f"{row['total']:.2f}",
            ]
            for row in worst_rows
        ]
        or [["n/a", "0", "0.00", "0.00"]],
    )
    return "\n".join(
        [
            f"# Diagnosis Packet: {summary['run_dir']}",
            "",
            "## Primary Read",
            "",
            f"- Most likely dominant issue: `{likely_failure}`",
            f"- Total PnL: `{summary['total_pnl']:.2f}` with drawdown `{summary['total_drawdown']:.2f}`",
            f"- Aggressive edge h5 average: `{(aggressive_edge / aggressive_qty) if aggressive_qty else 0.0:.3f}`",
            f"- Passive edge h5 average: `{(passive_edge / passive_qty) if passive_qty else 0.0:.3f}`",
            "",
            "## Failure Mode Ranking",
            "",
            "\n".join(
                f"- `{item['category']}`: {item['evidence']}" for item in categories[:5]
            )
            or "- No category evidence available.",
            "",
            "## Worst Timestamps",
            "",
            worst_table,
            "",
            "## Use This Packet For",
            "",
            "- Implementation chats: focus on one dominant failure mode only.",
            "- Diagnosis chats: use the headline metrics, inventory summary, fill summary, and worst timestamps.",
            "- Validation chats: compare this packet against a baseline run on the same dataset.",
            "",
            "## Local Limits",
            "",
            "- Local run artifacts are derived evidence, not canonical market data.",
            "- Conversion-heavy behavior may not be faithfully simulated locally; do not overclaim from conversion PnL.",
            "- Missing bundle data weakens state and inventory diagnosis confidence.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    run_dir = resolve_run_dir(args.run, args.set)
    summary = load_run_summary(run_dir)
    categories = diagnose_categories(summary)

    date_prefix = timestamp_slug()[:8]
    packet_id = args.packet_id or f"{date_prefix}_{run_dir.name}"
    packet_dir = ensure_directory(RESEARCH_ROOT / "05_execution_risk" / "diagnosis_packets" / packet_id)
    baselines_dir = ensure_directory(RESEARCH_ROOT / "06_validation" / "baselines")

    worst_rows = summary["worst_timestamps"]
    inventory = inventory_rows(summary)
    fills = fill_rows(summary)
    worst_fields = ["set", "timestamp", "delta_total", "total"]
    for row in worst_rows:
        for key in row:
            if key not in worst_fields:
                worst_fields.append(key)

    (packet_dir / "diagnosis_packet.md").write_text(
        build_diagnosis_packet_md(summary, categories),
        encoding="utf-8",
    )
    (baselines_dir / f"{packet_id}_run_summary.md").write_text(
        build_run_summary_md(summary, categories),
        encoding="utf-8",
    )
    write_json(baselines_dir / f"{packet_id}_headline_metrics.json", headline_metrics(summary))
    write_csv(
        packet_dir / "worst_timestamps.csv",
        worst_fields,
        worst_rows,
    )
    write_csv(
        packet_dir / "inventory_summary.csv",
        [
            "product",
            "max_long",
            "max_short",
            "max_abs",
            "avg_abs_position",
            "near_limit_fraction",
            "final_position_last_set",
            "pnl",
        ],
        inventory,
    )
    write_csv(
        packet_dir / "fill_summary.csv",
        [
            "product",
            "fill_kind",
            "side",
            "fill_count",
            "quantity",
            "avg_price",
            "edge_h5_avg",
            "edge_h20_avg",
        ],
        fills,
    )

    print(f"packet_dir: {packet_dir.relative_to(RESEARCH_ROOT.parent)}")
    print(f"run_summary: {(baselines_dir / f'{packet_id}_run_summary.md').relative_to(RESEARCH_ROOT.parent)}")
    print(
        f"headline_metrics: {(baselines_dir / f'{packet_id}_headline_metrics.json').relative_to(RESEARCH_ROOT.parent)}"
    )


if __name__ == "__main__":
    main()
