#!/usr/bin/env python3
"""Shared helpers for the Prosperity workflow scripts."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
RUNS_ROOT = ROOT / "runs"
RESEARCH_ROOT = REPO_ROOT / "prosperity-research"
CARGO = ROOT / "scripts" / "cargo_local.sh"

ROUND_ALIASES = {
    "tutorial": "tutorial",
    "tut": "tutorial",
    "round1": "round1",
    "r1": "round1",
    "1": "round1",
    "round2": "round2",
    "r2": "round2",
    "2": "round2",
    "round3": "round3",
    "r3": "round3",
    "3": "round3",
    "round4": "round4",
    "r4": "round4",
    "4": "round4",
    "round5": "round5",
    "r5": "round5",
    "5": "round5",
    "round6": "round6",
    "r6": "round6",
    "6": "round6",
    "round7": "round7",
    "r7": "round7",
    "7": "round7",
    "round8": "round8",
    "r8": "round8",
    "8": "round8",
}


@dataclass(frozen=True)
class DatasetSelection:
    cli_value: str
    label: str
    path: Path | None
    round_key: str | None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp_slug() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip())
    slug = slug.strip("-").lower()
    return slug or "unnamed"


def ensure_path(raw_path: str | Path, base: Path = ROOT) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()
    return (base / path).resolve()


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def git_commit() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def normalize_round_key(round_value: str | None) -> str:
    if round_value is None:
        return "round2"
    key = str(round_value).strip().lower()
    if key not in ROUND_ALIASES:
        raise ValueError(f"unsupported round '{round_value}'")
    return ROUND_ALIASES[key]


def resolve_dataset_selection(
    dataset: str | None = None,
    round_key: str | None = None,
) -> DatasetSelection:
    if dataset:
        raw = str(dataset).strip()
        lower = raw.lower()
        if lower in ROUND_ALIASES:
            resolved_round = ROUND_ALIASES[lower]
            path = ROOT / "datasets" / resolved_round
            return DatasetSelection(
                cli_value=str(path),
                label=resolved_round,
                path=path,
                round_key=resolved_round,
            )
        candidate = Path(raw)
        if candidate.is_absolute() or raw.startswith("datasets/") or (ROOT / raw).exists():
            path = ensure_path(raw)
            label = slugify(path.stem if path.is_file() else path.name)
            return DatasetSelection(
                cli_value=str(path),
                label=label,
                path=path,
                round_key=path.name if path.is_dir() else None,
            )
        return DatasetSelection(
            cli_value=raw,
            label=slugify(raw),
            path=None,
            round_key=ROUND_ALIASES.get(lower),
        )

    resolved_round = normalize_round_key(round_key)
    path = ROOT / "datasets" / resolved_round
    return DatasetSelection(
        cli_value=str(path),
        label=resolved_round,
        path=path,
        round_key=resolved_round,
    )


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run_command(command: Sequence[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed\n"
            f"cwd: {cwd}\n"
            f"cmd: {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return completed


def build_backtester_command(
    *,
    trader_path: Path,
    dataset_value: str,
    output_root: Path,
    run_id: str,
    artifact_mode: str | None = None,
    day: int | None = None,
    carry: bool = False,
    flat: bool = False,
    extra_args: Iterable[str] | None = None,
) -> list[str]:
    command = [
        str(CARGO),
        "run",
        "--",
        "--trader",
        str(trader_path),
        "--dataset",
        dataset_value,
        "--output-root",
        str(output_root),
        "--run-id",
        run_id,
    ]
    if artifact_mode:
        command.extend(["--artifact-mode", artifact_mode])
    if day is not None:
        command.append(f"--day={day}")
    if carry:
        command.append("--carry")
    if flat:
        command.append("--flat")
    if extra_args:
        command.extend(extra_args)
    return command


def discover_submission_logs(run_dir: Path) -> list[Path]:
    matches = {path.resolve() for path in run_dir.rglob("submission.log")}
    matches.update(path.resolve() for path in run_dir.glob("*-submission.log"))
    return sorted(matches)


def discover_inspection_files(run_dir: Path) -> list[Path]:
    preferred = []
    for name in ("combined.log", "bundle.json", "metrics.json"):
        preferred.extend(sorted(run_dir.rglob(name)))
        preferred.extend(sorted(run_dir.glob(f"*-{name}")))
    seen: set[Path] = set()
    ordered: list[Path] = []
    for path in preferred:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(resolved)
    return ordered
