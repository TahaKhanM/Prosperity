#!/usr/bin/env python3
"""Update the durable experiment registry from a completed run."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from diagnostics.common import load_run_summary
from workflow_common import RESEARCH_ROOT, ensure_directory, ensure_path, read_json


REGISTRY_PATH = RESEARCH_ROOT / "10_experiment_logs" / "experiment_registry.csv"
SUMMARY_PATH = RESEARCH_ROOT / "10_experiment_logs" / "latest_experiment_summary.md"
FIELDNAMES = [
    "timestamp",
    "trader_path",
    "baseline_trader_path",
    "dataset",
    "day",
    "hypothesis_tag",
    "strategy_family_tag",
    "total_pnl",
    "per_product_pnl",
    "drawdown",
    "run_folder",
    "ship_reject_status",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True, help="Harness run root created by scripts/run_harness.py.")
    parser.add_argument("--hypothesis-tag", default="unspecified", help="Short hypothesis tag.")
    parser.add_argument("--strategy-family-tag", default="unspecified", help="Short strategy family tag.")
    parser.add_argument(
        "--ship-reject-status",
        choices=("ship", "reject", "hold", "needs-review"),
        default="needs-review",
        help="Current decision status for the experiment.",
    )
    return parser.parse_args()


def read_registry_rows() -> list[dict[str, str]]:
    if not REGISTRY_PATH.is_file():
        return []
    with REGISTRY_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_registry_rows(rows: list[dict[str, str]]) -> None:
    ensure_directory(REGISTRY_PATH.parent)
    with REGISTRY_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def dataset_and_day(manifest: dict) -> tuple[str, str]:
    dataset = manifest.get("dataset", {})
    dataset_path = dataset.get("path") or dataset.get("cli_value") or "unknown"
    day = dataset.get("day")
    return str(dataset_path), "" if day is None else str(day)


def load_manifest(run_root: Path) -> dict:
    manifest_path = run_root / "run_manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing run manifest: {manifest_path}")
    return read_json(manifest_path)


def summarize_registry(rows: list[dict[str, str]]) -> str:
    latest_rows = list(reversed(rows[-5:]))
    ship_count = sum(1 for row in rows if row["ship_reject_status"] == "ship")
    reject_count = sum(1 for row in rows if row["ship_reject_status"] == "reject")
    needs_review = sum(1 for row in rows if row["ship_reject_status"] not in {"ship", "reject"})
    lines = [
        "# Latest Experiment Summary",
        "",
        f"- Registry entries: `{len(rows)}`",
        f"- Ship: `{ship_count}`",
        f"- Reject: `{reject_count}`",
        f"- Needs review / hold: `{needs_review}`",
        "",
        "## Most Recent Entries",
        "",
    ]
    if not latest_rows:
        lines.append("- No experiments registered yet.")
        return "\n".join(lines) + "\n"

    for row in latest_rows:
        lines.extend(
            [
                f"### {row['timestamp']}",
                f"- Trader: `{row['trader_path']}`",
                f"- Dataset/day: `{row['dataset']}` / `{row['day'] or 'all'}`",
                f"- Hypothesis: `{row['hypothesis_tag']}`",
                f"- Strategy family: `{row['strategy_family_tag']}`",
                f"- Total PnL: `{row['total_pnl']}`",
                f"- Drawdown: `{row['drawdown']}`",
                f"- Status: `{row['ship_reject_status']}`",
                f"- Run folder: `{row['run_folder']}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    run_root = ensure_path(args.run_root)
    manifest = load_manifest(run_root)
    candidate_dir = run_root / "candidate"
    if not candidate_dir.is_dir():
        raise SystemExit(f"missing candidate run directory: {candidate_dir}")
    candidate_summary = load_run_summary(candidate_dir)

    dataset_path, day = dataset_and_day(manifest)
    trader_path = str(manifest.get("trader_path") or "")
    baseline_trader_path = str(manifest.get("baseline_path") or "")
    per_product_pnl = json.dumps(
        {product: round(float(values.get("pnl", 0.0)), 4) for product, values in candidate_summary["products"].items()},
        sort_keys=True,
    )
    row = {
        "timestamp": str(manifest.get("created_at") or ""),
        "trader_path": trader_path,
        "baseline_trader_path": baseline_trader_path,
        "dataset": dataset_path,
        "day": day,
        "hypothesis_tag": args.hypothesis_tag,
        "strategy_family_tag": args.strategy_family_tag,
        "total_pnl": f"{candidate_summary['total_pnl']:.4f}",
        "per_product_pnl": per_product_pnl,
        "drawdown": f"{candidate_summary['total_drawdown']:.4f}",
        "run_folder": str(run_root.relative_to(RESEARCH_ROOT.parent)),
        "ship_reject_status": args.ship_reject_status,
    }

    rows = read_registry_rows()
    updated = False
    for index, existing in enumerate(rows):
        if existing["run_folder"] == row["run_folder"]:
            rows[index] = row
            updated = True
            break
    if not updated:
        rows.append(row)
    rows.sort(key=lambda item: item["timestamp"])

    write_registry_rows(rows)
    SUMMARY_PATH.write_text(summarize_registry(rows), encoding="utf-8")

    print(f"registry_csv: {REGISTRY_PATH.relative_to(RESEARCH_ROOT.parent)}")
    print(f"summary_md: {SUMMARY_PATH.relative_to(RESEARCH_ROOT.parent)}")


if __name__ == "__main__":
    main()
