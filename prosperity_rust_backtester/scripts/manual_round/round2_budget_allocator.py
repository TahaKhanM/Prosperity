#!/usr/bin/env python3
"""Evaluate Round 2 manual allocations across Research, Scale, and Speed."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from workflow_common import RESEARCH_ROOT, ensure_directory, ensure_path, timestamp_slug, write_csv


DEFAULT_SCENARIOS = [
    {"name": "speed_light", "speeds": [5, 8, 10, 12, 15, 18, 20]},
    {"name": "speed_cluster_20", "speeds": [10, 15, 18, 20, 20, 22, 25, 30]},
    {"name": "speed_heavy", "speeds": [20, 25, 30, 35, 40, 45, 50]},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario-file", help="Optional JSON file with competitor speed scenarios.")
    parser.add_argument("--step", type=int, default=5, help="Allocation grid step in percentage points.")
    parser.add_argument("--top-k", type=int, default=10, help="How many allocations to keep per scenario.")
    parser.add_argument("--run-id", help="Optional output folder id.")
    return parser.parse_args()


def load_scenarios(path_value: str | None) -> tuple[float, list[dict[str, object]]]:
    if not path_value:
        return 50_000.0, DEFAULT_SCENARIOS
    path = ensure_path(path_value, base=RESEARCH_ROOT.parent)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return float(payload.get("budget", 50_000.0)), list(payload.get("competitor_scenarios", DEFAULT_SCENARIOS))


def research_value(allocation: int) -> float:
    return 200_000.0 * math.log(1 + allocation) / math.log(101)


def scale_value(allocation: int) -> float:
    return 7.0 * allocation / 100.0


def speed_value(our_speed: int, competitor_speeds: list[int]) -> float:
    population = sorted([our_speed, *competitor_speeds], reverse=True)
    grouped: dict[int, list[int]] = {}
    for index, speed in enumerate(population, start=1):
        grouped.setdefault(speed, []).append(index)
    avg_rank = sum(grouped[our_speed]) / len(grouped[our_speed])
    if len(population) == 1:
        return 0.9
    return 0.9 - (avg_rank - 1.0) * (0.8 / (len(population) - 1))


def enumerate_allocations(step: int) -> list[tuple[int, int, int]]:
    allocations = []
    for research in range(0, 101, step):
        for scale in range(0, 101 - research, step):
            for speed in range(0, 101 - research - scale, step):
                allocations.append((research, scale, speed))
    return allocations


def scenario_rows(budget: float, scenarios: list[dict[str, object]], step: int, top_k: int) -> tuple[list[dict[str, object]], dict[str, list[dict[str, object]]]]:
    top_by_scenario: dict[str, list[dict[str, object]]] = {}
    all_rows: list[dict[str, object]] = []
    allocations = enumerate_allocations(step)
    for scenario in scenarios:
        name = str(scenario["name"])
        competitor_speeds = [int(value) for value in scenario["speeds"]]
        ranked: list[dict[str, object]] = []
        for research_pct, scale_pct, speed_pct in allocations:
            used_budget = budget * (research_pct + scale_pct + speed_pct) / 100.0
            r_value = research_value(research_pct)
            s_value = scale_value(scale_pct)
            sp_value = speed_value(speed_pct, competitor_speeds)
            pnl = (r_value * s_value * sp_value) - used_budget
            ranked.append(
                {
                    "scenario": name,
                    "research_pct": research_pct,
                    "scale_pct": scale_pct,
                    "speed_pct": speed_pct,
                    "budget_used": round(used_budget, 4),
                    "research_value": round(r_value, 4),
                    "scale_value": round(s_value, 4),
                    "speed_value": round(sp_value, 4),
                    "pnl": round(pnl, 4),
                }
            )
        ranked.sort(key=lambda row: float(row["pnl"]), reverse=True)
        top_by_scenario[name] = ranked[:top_k]
        all_rows.extend(ranked[:top_k])
    return all_rows, top_by_scenario


def robust_recommendation(top_by_scenario: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    aggregate: dict[tuple[int, int, int], list[float]] = {}
    for rows in top_by_scenario.values():
        for row in rows:
            key = (int(row["research_pct"]), int(row["scale_pct"]), int(row["speed_pct"]))
            aggregate.setdefault(key, []).append(float(row["pnl"]))
    if not aggregate:
        return {
            "research_pct": 0,
            "scale_pct": 0,
            "speed_pct": 0,
            "mean_pnl": 0.0,
            "worst_case_pnl": 0.0,
        }
    key, pnls = max(
        aggregate.items(),
        key=lambda item: (sum(item[1]) / len(item[1]), min(item[1])),
    )
    return {
        "research_pct": key[0],
        "scale_pct": key[1],
        "speed_pct": key[2],
        "mean_pnl": round(sum(pnls) / len(pnls), 4),
        "worst_case_pnl": round(min(pnls), 4),
    }


def build_recommendations_md(
    budget: float,
    scenarios: list[dict[str, object]],
    top_by_scenario: dict[str, list[dict[str, object]]],
    robust: dict[str, object],
) -> str:
    lines = [
        "# Recommended Allocations",
        "",
        f"- Budget assumption: `{budget:.0f}` XIRECs",
        "- Objective: `(Research × Scale × Speed) - Budget_Used`",
        "- Research follows the documented logarithmic curve and Scale is linear to 7.",
        "- Speed is scored from rank against the scenario competitor speeds.",
        "",
        "## Scenario Winners",
        "",
    ]
    for scenario in scenarios:
        name = str(scenario["name"])
        best = top_by_scenario[name][0]
        lines.extend(
            [
                f"### {name}",
                f"- Recommended allocation: Research `{best['research_pct']}` / Scale `{best['scale_pct']}` / Speed `{best['speed_pct']}`",
                f"- Expected PnL: `{best['pnl']}`",
                f"- Speed competitors: `{', '.join(str(int(value)) for value in scenario['speeds'])}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Robust Cross-Scenario Choice",
            "",
            (
                f"- Research `{robust['research_pct']}` / Scale `{robust['scale_pct']}` / "
                f"Speed `{robust['speed_pct']}`"
            ),
            f"- Mean PnL across retained scenarios: `{robust['mean_pnl']}`",
            f"- Worst retained scenario PnL: `{robust['worst_case_pnl']}`",
            "",
        ]
    )
    return "\n".join(lines)


def build_assumptions_md(budget: float, scenarios: list[dict[str, object]], step: int, scenario_file: str | None) -> str:
    lines = [
        "# Assumptions",
        "",
        f"- Budget: `{budget:.0f}` XIRECs",
        f"- Grid step: `{step}` percentage points",
        "- Research formula: `200_000 * log(1 + x) / log(101)`",
        "- Scale formula: `7 * x / 100`",
        "- Budget used: `budget * (research + scale + speed) / 100`",
        "- Speed scoring: rank-based from `0.9` (highest) to `0.1` (lowest), ties share the same average rank.",
        f"- Scenario source: `{scenario_file or 'built-in defaults'}`",
        "",
        "## Competitor Speed Scenarios",
        "",
    ]
    for scenario in scenarios:
        lines.append(f"- `{scenario['name']}`: {', '.join(str(int(value)) for value in scenario['speeds'])}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    budget, scenarios = load_scenarios(args.scenario_file)
    run_id = args.run_id or timestamp_slug()
    output_dir = ensure_directory(RESEARCH_ROOT / "07_manual_round" / "round2_budget" / run_id)

    scenario_table, top_by_scenario = scenario_rows(budget, scenarios, args.step, args.top_k)
    robust = robust_recommendation(top_by_scenario)
    write_csv(
        output_dir / "scenario_table.csv",
        [
            "scenario",
            "research_pct",
            "scale_pct",
            "speed_pct",
            "budget_used",
            "research_value",
            "scale_value",
            "speed_value",
            "pnl",
        ],
        scenario_table,
    )
    (output_dir / "recommended_allocations.md").write_text(
        build_recommendations_md(budget, scenarios, top_by_scenario, robust),
        encoding="utf-8",
    )
    (output_dir / "assumptions.md").write_text(
        build_assumptions_md(budget, scenarios, args.step, args.scenario_file),
        encoding="utf-8",
    )

    print(f"output_dir: {output_dir.relative_to(RESEARCH_ROOT.parent)}")
    print(f"scenario_table: {(output_dir / 'scenario_table.csv').relative_to(RESEARCH_ROOT.parent)}")
    print(f"recommended_allocations: {(output_dir / 'recommended_allocations.md').relative_to(RESEARCH_ROOT.parent)}")


if __name__ == "__main__":
    main()
