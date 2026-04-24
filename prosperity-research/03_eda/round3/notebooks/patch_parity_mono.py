"""Re-run axis H monotonicity with corrected sign.

Monotonicity: V_{K1} >= V_{K2} for K1 < K2.
Violation (tradeable): best_ask(K1) < best_bid(K2) - edge  => buy K1, sell K2.

Also compute tradeable floor with S_bid (must sell VE to hedge), not S_ask.
"""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
DATA = REPO / "Data" / "ROUND_3"
sys.path.append(str(Path(__file__).resolve().parent))
from alpha_hunt import load_prices_day, STRIKES, DAYS

OUT = Path(__file__).resolve().parent / "_cache" / "parity_corrected.json"
OUT.parent.mkdir(parents=True, exist_ok=True)


def main():
    result = {"per_day": {}}
    for d in DAYS:
        day_data = load_prices_day(d)
        ve = day_data["VELVETFRUIT_EXTRACT"]
        S_bid = ve["b1"]; S_ask = ve["a1"]
        voucher_arrs = {k: day_data[f"VEV_{k}"] for k in STRIKES}

        counts = {"floor_sbid": 0, "floor_sask": 0, "cap": 0, "mono": 0, "butterfly": 0}
        edges = {c: [] for c in counts}

        # Floor: buy voucher, sell VE. Need best_ask(K) < best_bid(S) - K.
        # Conservative variant: best_ask(K) < max(S_bid - K, 0).
        for k, arr in voucher_arrs.items():
            a_v = arr["a1"]
            b_v = arr["b1"]
            intrinsic_bid = np.maximum(S_bid - k, 0.0)
            intrinsic_ask = np.maximum(S_ask - k, 0.0)
            mask_b = np.isfinite(a_v) & np.isfinite(S_bid) & (intrinsic_bid - a_v >= 1)
            mask_a = np.isfinite(a_v) & np.isfinite(S_ask) & (intrinsic_ask - a_v >= 1)
            counts["floor_sbid"] += int(mask_b.sum())
            counts["floor_sask"] += int(mask_a.sum())
            edges["floor_sbid"].extend((intrinsic_bid - a_v)[mask_b].tolist())
            edges["floor_sask"].extend((intrinsic_ask - a_v)[mask_a].tolist())
            # Cap: V_K <= S. Violation: best_bid(K) > S_ask + edge.
            mask_c = np.isfinite(b_v) & np.isfinite(S_ask) & (b_v - S_ask >= 1)
            counts["cap"] += int(mask_c.sum())
            edges["cap"].extend((b_v - S_ask)[mask_c].tolist())

        # Monotonicity VIOLATION: for K1 < K2, V_{K1} < V_{K2}.
        # Tradeable: best_ask(K1) < best_bid(K2) - edge.
        strikes_sorted = sorted(voucher_arrs.keys())
        for i, k1 in enumerate(strikes_sorted):
            for k2 in strikes_sorted[i + 1:]:
                a1 = voucher_arrs[k1]["a1"]
                b2 = voucher_arrs[k2]["b1"]
                mask = np.isfinite(a1) & np.isfinite(b2) & (b2 - a1 >= 1)
                counts["mono"] += int(mask.sum())
                edges["mono"].extend((b2 - a1)[mask].tolist())

        # Butterfly: consecutive equally-spaced strikes (5000,5100,5200)..
        # Check V_{K1} - 2 V_{K2} + V_{K3} >= 0.
        # Tradeable violation: best_bid(K1) - 2 best_ask(K2) + best_bid(K3) < -edge  OR reverse.
        equal_triples = [
            (5000, 5100, 5200), (5100, 5200, 5300), (5200, 5300, 5400),
            (5300, 5400, 5500),
        ]
        for (k1, k2, k3) in equal_triples:
            a1 = voucher_arrs[k1]["a1"]; b1 = voucher_arrs[k1]["b1"]
            a2 = voucher_arrs[k2]["a1"]; b2 = voucher_arrs[k2]["b1"]
            a3 = voucher_arrs[k3]["a1"]; b3 = voucher_arrs[k3]["b1"]
            # buy wings, sell middle: a1 + a3 - 2*b2 < 0 means wings cheap / middle rich
            val = a1 + a3 - 2.0 * b2
            mask = np.isfinite(val) & (val <= -1)
            counts["butterfly"] += int(mask.sum())
            edges["butterfly"].extend((-val)[mask].tolist())

        result["per_day"][d] = {
            "counts": counts,
            "edge_stats": {
                c: {
                    "n": len(edges[c]),
                    "mean": float(np.mean(edges[c])) if edges[c] else 0.0,
                    "max": float(np.max(edges[c])) if edges[c] else 0.0,
                    "sum": float(np.sum(edges[c])) if edges[c] else 0.0,
                }
                for c in counts
            },
        }

    with open(OUT, "w") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
