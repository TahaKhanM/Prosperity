#!/usr/bin/env python3
import itertools
import os
import re
import subprocess
from typing import Dict, List, Tuple


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKTESTER = os.path.join(ROOT, "target", "release", "rust_backtester")
TRADER = "traders/research_param_trader.py"
ROW_RE = re.compile(r"^(D-2|D-1|SUB)\s+[-\d]+\s+\d+\s+\d+\s+([-\d.]+)", re.M)


def parse_output(output: str) -> Tuple[Dict[str, float], Dict[str, Tuple[float, float, float]]]:
    rows = {match.group(1): float(match.group(2)) for match in ROW_RE.finditer(output)}
    products: Dict[str, Tuple[float, float, float]] = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0] in ("TOM", "EMR"):
            products[parts[0]] = tuple(float(value) for value in parts[1:])  # type: ignore[assignment]
    return rows, products


def run_variant(env_updates: Dict[str, str]) -> Tuple[float, float, float, float, Dict[str, str]]:
    env = os.environ.copy()
    env.update(
        {
            "EM_OFFSETS": "7,6,5",
            "EM_SIZES": "25,20,20",
            "EM_SKEW": "0",
            "EM_TAKE_EDGE": "2",
            "TOM_MODE": "inside",
            "TOM_LEVELS": "1",
            "TOM_SIZES": "5",
            "TOM_FAIR": "signal",
            "TOM_SPAN": "1",
        }
    )
    env.update(env_updates)

    completed = subprocess.run(
        [
            BACKTESTER,
            "--trader",
            TRADER,
            "--dataset",
            "tutorial",
            "--artifact-mode",
            "none",
            "--products",
            "full",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    rows, products = parse_output(completed.stdout)
    return rows["SUB"], rows["D-1"], rows["D-2"], products["TOM"][2], env_updates


def main() -> None:
    coefficient_sets = [
        ("0.5", "-0.5", "-0.4"),
        ("0.25", "-0.5", "-0.4"),
        ("0.75", "-0.5", "-0.3"),
        ("1", "-0.5", "-0.2"),
    ]
    variants: List[Tuple[float, float, float, float, Dict[str, str]]] = []

    for (micro_wt, ret_wt, z_wt), take_edge, passive_edge, skew in itertools.product(
        coefficient_sets,
        ("2", "2.5", "3"),
        ("1.5", "2", "2.5"),
        ("0", "0.01"),
    ):
        variants.append(
            run_variant(
                {
                    "TOM_MICRO_SIG_WT": micro_wt,
                    "TOM_RET1_WT": ret_wt,
                    "TOM_Z20_WT": z_wt,
                    "TOM_TAKE_EDGE": take_edge,
                    "TOM_MIN_EDGE": passive_edge,
                    "TOM_SKEW": skew,
                }
            )
        )

    variants.sort(key=lambda row: (row[0], row[1], row[2], row[3]), reverse=True)
    print("SUB,D-1,D-2,TOM_SUB,PARAMS")
    for sub, day_1, day_2, tom_sub, params in variants[:20]:
        print(f"{sub:.2f},{day_1:.2f},{day_2:.2f},{tom_sub:.2f},{params}")


if __name__ == "__main__":
    main()
