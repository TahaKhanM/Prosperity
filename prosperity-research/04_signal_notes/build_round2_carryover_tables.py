#!/usr/bin/env python3
"""Build Round 1 vs Round 2 carryover tables from the analyzer outputs."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ANALYZER_DIR = ROOT / "prosperity-research" / "03_eda" / "round1"
SNAPSHOT_DIR = ANALYZER_DIR / "ai_strategy_context_by_round"
OUTPUT_DIR = ROOT / "prosperity-research" / "04_signal_notes"

ROUND_KEYS = ("round1", "round2")
SIGNALS = (
    "wall_delta",
    "mm_delta",
    "micro_delta",
    "z20",
    "ret1",
    "imbalance",
    "imb_l1",
    "ofi_5",
    "spread_chg",
)


def load_analysis_module():
    spec = importlib.util.spec_from_file_location("prosperity_analysis", ANALYZER_DIR / "analysis.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_snapshot(round_key: str) -> dict:
    path = SNAPSHOT_DIR / round_key / "product_params.json"
    return json.loads(path.read_text())


def build_metric_comparison(snapshots: dict[str, dict]) -> pd.DataFrame:
    rows = []
    metrics = (
        ("classification", lambda e: e["classification"]),
        ("archetype", lambda e: e["archetype"]["primary"]),
        ("best_fair", lambda e: e["fair_value"]["best"]),
        ("lag1_acf", lambda e: e["mean_reversion"]["lag1_acf"]),
        ("best_signal", lambda e: e["best_signal"]),
        ("best_signal_corr", lambda e: e["best_signal_corr"]),
        ("take_edge", lambda e: e["spread"]["take_edge"]),
        ("passive_edge", lambda e: e["spread"]["passive_edge"]),
        ("spread_mean", lambda e: e["spread"]["mean"]),
        ("spread_p50", lambda e: e["spread"]["p50"]),
        ("imb_l1_std", lambda e: e["microstructure"]["imb_l1_std"]),
        ("ofi_std", lambda e: e["microstructure"]["ofi_std"]),
        ("micro_minus_mid_std", lambda e: e["microstructure"]["micro_minus_mid_std"]),
        ("n_buy_takes", lambda e: e["execution"]["n_buy_takes"]),
        ("n_sell_takes", lambda e: e["execution"]["n_sell_takes"]),
        ("buy_markout_h5", lambda e: e["execution"]["buy_markout_h5"]),
        ("sell_markout_h5", lambda e: e["execution"]["sell_markout_h5"]),
        ("spike_freq_10k", lambda e: e["spikes"]["per_10k_ticks"]),
        ("spike_reversion", lambda e: e["spikes"]["reversion_tradeable"]),
        ("sim_pct_at_limit", lambda e: e["simulation"]["pct_at_limit"]),
        ("sim_mtm_pnl", lambda e: e["simulation"]["mtm_pnl"]),
        ("ols_r2", lambda e: e["feature_relevance"]["r2"]),
    )

    products = snapshots["round1"]["products"].keys()
    for product in products:
        r1 = snapshots["round1"]["products"][product]
        r2 = snapshots["round2"]["products"][product]
        for metric, getter in metrics:
            rows.append(
                {
                    "product": product,
                    "metric": metric,
                    "round1": getter(r1),
                    "round2": getter(r2),
                }
            )

    return pd.DataFrame(rows)


def build_fair_proxy_comparison(snapshots: dict[str, dict]) -> pd.DataFrame:
    rows = []
    products = snapshots["round1"]["products"].keys()
    for product in products:
        stds1 = snapshots["round1"]["products"][product]["fair_value"]["stds"]
        stds2 = snapshots["round2"]["products"][product]["fair_value"]["stds"]
        rank1 = {name: rank for rank, (name, _) in enumerate(sorted(stds1.items(), key=lambda kv: kv[1]), start=1)}
        rank2 = {name: rank for rank, (name, _) in enumerate(sorted(stds2.items(), key=lambda kv: kv[1]), start=1)}
        for proxy in sorted(stds1.keys()):
            rows.append(
                {
                    "product": product,
                    "proxy": proxy,
                    "round1_std": stds1.get(proxy),
                    "round2_std": stds2.get(proxy),
                    "round1_rank": rank1.get(proxy),
                    "round2_rank": rank2.get(proxy),
                    "round1_best": snapshots["round1"]["products"][product]["fair_value"]["best"],
                    "round2_best": snapshots["round2"]["products"][product]["fair_value"]["best"],
                }
            )
    return pd.DataFrame(rows)


def compute_signal_tables(analysis_module) -> pd.DataFrame:
    per_round = {}
    per_day_rows = []

    for round_key in ROUND_KEYS:
        analysis_module.configure_round(round_key)
        products, product_dfs, _ = analysis_module.load_data()
        feat_dfs = {product: analysis_module.compute_features(df) for product, df in product_dfs.items()}
        per_round[round_key] = {}

        for product, df in feat_dfs.items():
            per_round[round_key][product] = {}
            for signal in SIGNALS:
                pair = df[[signal, "fwd_ret_1"]].dropna()
                corr = pair[signal].corr(pair["fwd_ret_1"]) if len(pair) else None
                per_round[round_key][product][signal] = corr
                for day in sorted(df["day"].unique()):
                    dd = df[df["day"] == day][[signal, "fwd_ret_1"]].dropna()
                    day_corr = dd[signal].corr(dd["fwd_ret_1"]) if len(dd) else None
                    per_day_rows.append(
                        {
                            "round": round_key,
                            "product": product,
                            "signal": signal,
                            "day": int(day),
                            "corr_h1": day_corr,
                        }
                    )

    per_day_df = pd.DataFrame(per_day_rows)
    rows = []
    for product in per_round["round1"]:
        ranks = {}
        for round_key in ROUND_KEYS:
            ranked = sorted(
                per_round[round_key][product].items(),
                key=lambda kv: abs(kv[1]) if kv[1] is not None else -1,
                reverse=True,
            )
            ranks[round_key] = {signal: rank for rank, (signal, _) in enumerate(ranked, start=1)}

        for signal in SIGNALS:
            r1 = per_round["round1"][product][signal]
            r2 = per_round["round2"][product][signal]
            per_day_1 = per_day_df[
                (per_day_df["round"] == "round1")
                & (per_day_df["product"] == product)
                & (per_day_df["signal"] == signal)
            ]["corr_h1"].dropna()
            per_day_2 = per_day_df[
                (per_day_df["round"] == "round2")
                & (per_day_df["product"] == product)
                & (per_day_df["signal"] == signal)
            ]["corr_h1"].dropna()

            sign_consistent = None
            if r1 is not None and r2 is not None and r1 != 0 and r2 != 0:
                sign_consistent = (r1 > 0) == (r2 > 0)

            def classify_carryover() -> str:
                a1 = abs(r1) if r1 is not None else 0.0
                a2 = abs(r2) if r2 is not None else 0.0
                if a1 < 0.02 and a2 < 0.02:
                    return "weak_both_rounds"
                if a1 >= 0.05 and a2 >= 0.05 and sign_consistent:
                    ratio = a2 / a1 if a1 else 0.0
                    if 0.67 <= ratio <= 1.5:
                        return "carries_over_directly"
                    return "carries_over_with_retuning"
                if a1 < 0.05 and a2 >= 0.05:
                    return "stronger_in_round2"
                if a1 >= 0.05 and a2 < 0.05:
                    return "weaker_in_round2"
                if sign_consistent is False:
                    return "sign_flip"
                return "mixed"

            rows.append(
                {
                    "product": product,
                    "signal": signal,
                    "round1_corr_h1": r1,
                    "round2_corr_h1": r2,
                    "round1_abs_rank": ranks["round1"][signal],
                    "round2_abs_rank": ranks["round2"][signal],
                    "sign_consistent": sign_consistent,
                    "round1_day_min_corr": per_day_1.min() if not per_day_1.empty else None,
                    "round1_day_max_corr": per_day_1.max() if not per_day_1.empty else None,
                    "round2_day_min_corr": per_day_2.min() if not per_day_2.empty else None,
                    "round2_day_max_corr": per_day_2.max() if not per_day_2.empty else None,
                    "round1_sign_flip_within_round": (per_day_1.min() < 0 < per_day_1.max()) if not per_day_1.empty else None,
                    "round2_sign_flip_within_round": (per_day_2.min() < 0 < per_day_2.max()) if not per_day_2.empty else None,
                    "carryover_hint": classify_carryover(),
                }
            )

    return pd.DataFrame(rows)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    analysis_module = load_analysis_module()
    snapshots = {round_key: load_snapshot(round_key) for round_key in ROUND_KEYS}

    metric_df = build_metric_comparison(snapshots)
    fair_df = build_fair_proxy_comparison(snapshots)
    signal_df = compute_signal_tables(analysis_module)

    metric_df.to_csv(OUTPUT_DIR / "round2_round_comparison_metrics.csv", index=False)
    fair_df.to_csv(OUTPUT_DIR / "round2_fair_proxy_comparison.csv", index=False)
    signal_df.to_csv(OUTPUT_DIR / "round2_signal_carryover_matrix.csv", index=False)

    print("wrote", OUTPUT_DIR / "round2_round_comparison_metrics.csv")
    print("wrote", OUTPUT_DIR / "round2_fair_proxy_comparison.csv")
    print("wrote", OUTPUT_DIR / "round2_signal_carryover_matrix.csv")


if __name__ == "__main__":
    main()
