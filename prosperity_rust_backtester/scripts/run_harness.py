#!/usr/bin/env python3
"""Run explicit trader/dataset combinations with a stable manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from workflow_common import (
    RUNS_ROOT,
    build_backtester_command,
    discover_inspection_files,
    discover_submission_logs,
    ensure_directory,
    ensure_path,
    git_commit,
    repo_relative,
    resolve_dataset_selection,
    run_command,
    slugify,
    timestamp_slug,
    utc_now,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trader", required=True, help="Trader file to run.")
    parser.add_argument("--baseline", help="Optional baseline trader to run on the same dataset.")
    parser.add_argument(
        "--dataset",
        help="Explicit dataset alias or path. If omitted, the harness uses datasets/round2 explicitly.",
    )
    parser.add_argument("--round", help="Optional round alias when --dataset is omitted.")
    parser.add_argument("--day", type=int, help="Optional day filter passed through to the Rust CLI.")
    parser.add_argument(
        "--artifact-mode",
        choices=("none", "diagnostic", "submission", "full"),
        default="full",
        help="Artifact mode passed through to the Rust CLI.",
    )
    parser.add_argument("--carry", action="store_true", help="Enable carry mode.")
    parser.add_argument("--flat", action="store_true", help="Enable flat artifact layout.")
    parser.add_argument("--label", help="Optional stable label prefix for the top-level run folder.")
    return parser.parse_args()


def choose_run_root(label: str | None, trader_path: Path, dataset_label: str, day: int | None) -> Path:
    stem = label or f"{timestamp_slug()}_{trader_path.stem}_{dataset_label}"
    if day is not None:
        stem = f"{stem}_day{day}"
    run_root = RUNS_ROOT / slugify(stem)
    if run_root.exists():
        raise SystemExit(f"run folder already exists: {run_root}")
    return run_root


def execute_named_run(
    *,
    name: str,
    trader_path: Path,
    dataset_value: str,
    run_root: Path,
    artifact_mode: str,
    day: int | None,
    carry: bool,
    flat: bool,
) -> dict[str, object]:
    run_id = name
    command = build_backtester_command(
        trader_path=trader_path,
        dataset_value=dataset_value,
        output_root=run_root,
        run_id=run_id,
        artifact_mode=artifact_mode,
        day=day,
        carry=carry,
        flat=flat,
    )
    completed = run_command(command)
    run_dir = run_root / run_id
    submission_logs = discover_submission_logs(run_dir)
    inspection_files = discover_inspection_files(run_dir)
    return {
        "run_id": run_id,
        "run_dir": repo_relative(run_dir),
        "command": [str(part) for part in command],
        "stdout_tail": completed.stdout.strip().splitlines()[-10:],
        "visualizer_file": repo_relative(submission_logs[0]) if submission_logs else None,
        "inspection_file": repo_relative(inspection_files[0]) if inspection_files else None,
        "all_visualizer_files": [repo_relative(path) for path in submission_logs],
        "all_inspection_files": [repo_relative(path) for path in inspection_files],
    }


def main() -> None:
    args = parse_args()
    trader_path = ensure_path(args.trader)
    if not trader_path.is_file():
        raise SystemExit(f"missing trader: {trader_path}")

    baseline_path = ensure_path(args.baseline) if args.baseline else None
    if baseline_path and not baseline_path.is_file():
        raise SystemExit(f"missing baseline trader: {baseline_path}")

    dataset = resolve_dataset_selection(dataset=args.dataset, round_key=args.round)
    run_root = choose_run_root(args.label, trader_path, dataset.label, args.day)
    ensure_directory(run_root)

    manifest = {
        "created_at": utc_now().isoformat(),
        "git_commit": git_commit(),
        "dataset": {
            "label": dataset.label,
            "cli_value": dataset.cli_value,
            "path": repo_relative(dataset.path) if dataset.path else dataset.cli_value,
            "round_key": dataset.round_key,
            "day": args.day,
        },
        "artifact_mode": args.artifact_mode,
        "carry": bool(args.carry),
        "flat": bool(args.flat),
        "trader_path": repo_relative(trader_path),
        "baseline_path": repo_relative(baseline_path) if baseline_path else None,
        "runs": {},
    }

    manifest["runs"]["candidate"] = execute_named_run(
        name="candidate",
        trader_path=trader_path,
        dataset_value=dataset.cli_value,
        run_root=run_root,
        artifact_mode=args.artifact_mode,
        day=args.day,
        carry=args.carry,
        flat=args.flat,
    )
    if baseline_path:
        manifest["runs"]["baseline"] = execute_named_run(
            name="baseline",
            trader_path=baseline_path,
            dataset_value=dataset.cli_value,
            run_root=run_root,
            artifact_mode=args.artifact_mode,
            day=args.day,
            carry=args.carry,
            flat=args.flat,
        )

    write_json(run_root / "run_manifest.json", manifest)

    print(f"run_root: {repo_relative(run_root)}")
    print(f"dataset: {manifest['dataset']['path']}")
    print(f"artifact_mode: {args.artifact_mode}")
    print(f"candidate_run: {manifest['runs']['candidate']['run_dir']}")
    if baseline_path:
        print(f"baseline_run: {manifest['runs']['baseline']['run_dir']}")
    print(f"manifest: {repo_relative(run_root / 'run_manifest.json')}")

    candidate = manifest["runs"]["candidate"]
    visualizer_file = candidate.get("visualizer_file")
    inspection_file = candidate.get("inspection_file")
    if visualizer_file:
        print(f"local_visualizer: {visualizer_file}")
    else:
        print("local_visualizer: no submission.log produced for the candidate run")
    if inspection_file:
        print(f"inspection_file: {inspection_file}")
    else:
        print("inspection_file: no combined.log/bundle.json/metrics.json found for the candidate run")


if __name__ == "__main__":
    main()

